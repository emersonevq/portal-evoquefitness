import Layout from "@/components/layout/Layout";
import { sectors } from "@/data/sectors";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { useAuthContext } from "@/lib/auth-context";
import { Separator } from "@/components/ui/separator";
import { CheckCircle, Copy, AlertCircle } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useEffect, useMemo, useState } from "react";
import { apiFetch } from "@/lib/api";
import { motion, AnimatePresence } from "framer-motion";

const sector = sectors.find((s) => s.slug === "ti")!;

interface Ticket {
  id: string;
  codigo: string;
  protocolo: string;
  data: string;
  problema: string;
  status: string;
}

export default function TiPage() {
  const API_BASE: string = (import.meta as any)?.env?.VITE_API_BASE || "/api";
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [lastCreated, setLastCreated] = useState<{
    codigo: string;
    protocolo: string;
  } | null>(null);
  const [open, setOpen] = useState(false);
  const [successOpen, setSuccessOpen] = useState(false);
  const [unidades, setUnidades] = useState<
    { id: number; nome: string; cidade: string }[]
  >([]);
  const [problemas, setProblemas] = useState<
    { id: number; nome: string; prioridade: string; requer_internet: boolean }[]
  >([]);

  useEffect(() => {
    if (!open) return;
    apiFetch("/unidades")
      .then((r) => {
        if (!r.ok) return Promise.reject(new Error("fail"));
        return r.json();
      })
      .then((data) => {
        if (Array.isArray(data)) setUnidades(data);
        else setUnidades([]);
      })
      .catch((err) => {
        console.error("Error loading unidades:", err);
        setUnidades([]);
      });
    apiFetch("/problemas")
      .then((r) => {
        if (!r.ok) {
          console.error("Failed to load problemas:", r.status, r.statusText);
          return Promise.reject(new Error("fail"));
        }
        return r.json();
      })
      .then((data) => {
        if (Array.isArray(data)) setProblemas(data);
        else {
          console.error("Invalid problemas data format:", data);
          setProblemas([]);
        }
      })
      .catch((err) => {
        console.error("Error loading problemas:", err);
        setProblemas([]);
      });
  }, [open]);

  return (
    <Layout>
      <section className="w-full">
        <div className="brand-gradient">
          <div className="container py-10 sm:py-14">
            <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-primary-foreground drop-shadow">
              {sector.title}
            </h1>
            <p className="mt-2 text-primary-foreground/90 max-w-2xl">
              {sector.description}
            </p>
          </div>
        </div>
      </section>

      <section className="container py-8">
        {lastCreated && (
          <div className="mb-4 rounded-lg border border-border/60 bg-card p-4 text-sm">
            <div className="font-semibold mb-1">Chamado criado com sucesso</div>
            <div>
              Código <span className="font-semibold">{lastCreated.codigo}</span>{" "}
              e Protocolo{" "}
              <span className="font-semibold">{lastCreated.protocolo}</span>{" "}
              gerados e salvos.
            </div>
            <div className="text-muted-foreground mt-1">
              Guarde essas informações para futuras consultas.
            </div>
          </div>
        )}
        <div className="flex items-center justify-between gap-4">
          {/** show admin shortcut only to Administrador */}
          {(() => {
            const { user } = useAuthContext();
            return user?.nivel_acesso === "Administrador" ? (
              <div className="md:hidden">
                <Button asChild variant="secondary" className="rounded-full">
                  <Link to="/setor/ti/admin">Painel administrativo</Link>
                </Button>
              </div>
            ) : null;
          })()}
          <h2 className="text-lg sm:text-xl font-semibold">
            Histórico de chamados
          </h2>
          {(() => {
            const { user } = useAuthContext();
            return user?.nivel_acesso === "Administrador" ? (
              <div className="hidden md:block">
                <Button asChild className="mr-2 rounded-full">
                  <Link to="/setor/ti/admin">Painel administrativo</Link>
                </Button>
              </div>
            ) : null;
          })()}
          <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
              <Button className="rounded-full">Abrir novo chamado</Button>
            </DialogTrigger>
            <DialogContent className="max-w-xl">
              <DialogHeader>
                <DialogTitle>Abrir chamado</DialogTitle>
              </DialogHeader>
              <TicketForm
                problemas={problemas}
                unidades={unidades}
                onSubmit={async (payload) => {
                  try {
                    const fd = new FormData();
                    fd.set("solicitante", payload.nome);
                    fd.set("cargo", payload.cargo);
                    fd.set("email", payload.email);
                    fd.set("telefone", payload.telefone);
                    fd.set("unidade", payload.unidade);
                    fd.set("problema", payload.problema);
                    if (payload.internetItem)
                      fd.set("internetItem", payload.internetItem);
                    if (payload.descricao)
                      fd.set("descricao", payload.descricao);
                    if (payload.files && payload.files.length > 0) {
                      for (const f of payload.files) fd.append("files", f);
                    }
                    const res = await apiFetch("/chamados/with-attachments", {
                      method: "POST",
                      body: fd,
                    });
                    if (!res.ok) throw new Error("Falha ao criar chamado");
                    const created: {
                      id: number;
                      codigo: string;
                      protocolo: string;
                      data_abertura: string;
                      problema: string;
                      internet_item?: string | null;
                      status: string;
                    } = await res.json();

                    const problemaFmt =
                      created.problema === "Internet" && created.internet_item
                        ? `Internet - ${created.internet_item}`
                        : created.problema;

                    setTickets((prev) => [
                      {
                        id: String(created.id),
                        codigo: created.codigo,
                        protocolo: created.protocolo,
                        data:
                          created.data_abertura?.slice(0, 10) ||
                          new Date().toISOString().slice(0, 10),
                        problema: problemaFmt,
                        status: created.status,
                      },
                      ...prev,
                    ]);
                    setLastCreated({
                      codigo: created.codigo,
                      protocolo: created.protocolo,
                    });
                    setOpen(false);
                    setSuccessOpen(true);
                  } catch (e) {
                    console.error(e);
                    alert("Não foi possível abrir o chamado. Tente novamente.");
                  }
                }}
              />
            </DialogContent>
          </Dialog>
        </div>

        <div className="mt-4 overflow-x-auto rounded-xl border border-border/60 bg-card">
          <table className="w-full min-w-[720px] text-sm">
            <thead>
              <tr className="text-left">
                <th className="px-4 py-3 font-semibold">Código</th>
                <th className="px-4 py-3 font-semibold">Protocolo</th>
                <th className="px-4 py-3 font-semibold">Data</th>
                <th className="px-4 py-3 font-semibold">Problema</th>
                <th className="px-4 py-3 font-semibold">Status</th>
                <th className="px-4 py-3 font-semibold">Ações</th>
              </tr>
            </thead>
            <tbody>
              {tickets.length === 0 ? (
                <tr>
                  <td
                    className="px-4 py-6 text-center text-muted-foreground"
                    colSpan={6}
                  >
                    Você ainda não abriu nenhum chamado.
                  </td>
                </tr>
              ) : (
                tickets.map((t) => (
                  <tr key={t.id} className="border-t border-border/60">
                    <td className="px-4 py-3">{t.codigo}</td>
                    <td className="px-4 py-3">{t.protocolo}</td>
                    <td className="px-4 py-3">
                      {new Date(t.data).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3">{t.problema}</td>
                    <td className="px-4 py-3">{t.status}</td>
                    <td className="px-4 py-3">
                      <Button variant="secondary" size="sm">
                        Ver
                      </Button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>

      <AnimatePresence>
        {successOpen && lastCreated && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setSuccessOpen(false)}
              className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50"
            />
            <motion.div
              initial={{ scale: 0.8, opacity: 0, y: 20 }}
              animate={{ scale: 1, opacity: 1, y: 0 }}
              exit={{ scale: 0.8, opacity: 0, y: 20 }}
              transition={{ type: "spring", damping: 25, stiffness: 300 }}
              className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-lg z-50"
            >
              <div className="mx-4 rounded-2xl bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 border border-slate-700/50 shadow-2xl overflow-hidden">
                <div className="relative overflow-hidden">
                  <div className="absolute -right-20 -top-20 w-40 h-40 bg-primary/20 rounded-full blur-3xl" />
                  <div className="absolute -left-20 -bottom-20 w-40 h-40 bg-primary/10 rounded-full blur-3xl" />

                  <div className="relative p-8 sm:p-10">
                    <div className="flex items-start justify-between mb-8">
                      <motion.div
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        transition={{ type: "spring", delay: 0.2, damping: 20 }}
                        className="flex-shrink-0"
                      >
                        <div className="flex items-center justify-center w-16 h-16 rounded-full bg-gradient-to-br from-primary to-primary/70 shadow-lg">
                          <CheckCircle className="w-8 h-8 text-white" />
                        </div>
                      </motion.div>
                      <button
                        onClick={() => setSuccessOpen(false)}
                        className="text-slate-400 hover:text-white transition-colors"
                      >
                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    </div>

                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.3 }}
                      className="mb-8"
                    >
                      <h2 className="text-3xl font-bold text-white mb-2">
                        Chamado criado com sucesso!
                      </h2>
                      <p className="text-slate-400">
                        Seu chamado foi registrado no sistema. Guarde as informações abaixo para futuras consultas.
                      </p>
                    </motion.div>

                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.4 }}
                      className="mb-8 rounded-lg border border-amber-500/30 bg-amber-500/10 p-4"
                    >
                      <div className="flex gap-3">
                        <AlertCircle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
                        <div className="flex-1">
                          <div className="font-semibold text-amber-300 text-sm mb-1">
                            Importante: Guarde estas informações
                          </div>
                          <p className="text-sm text-amber-200/80">
                            O código e protocolo são essenciais para rastrear seu chamado.
                          </p>
                        </div>
                      </div>
                    </motion.div>

                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.5 }}
                      className="space-y-4 mb-8"
                    >
                      {[
                        { label: "Código", value: lastCreated.codigo },
                        { label: "Protocolo", value: lastCreated.protocolo }
                      ].map((item, idx) => (
                        <motion.div
                          key={item.label}
                          initial={{ opacity: 0, x: -10 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: 0.5 + idx * 0.1 }}
                          className="group"
                        >
                          <label className="text-sm font-medium text-slate-300 mb-2 block">
                            {item.label}
                          </label>
                          <div className="flex items-center gap-2">
                            <div className="flex-1 px-4 py-3 rounded-lg bg-slate-700/50 border border-slate-600/50 group-hover:border-primary/50 transition-colors">
                              <code className="text-white font-mono text-lg font-semibold tracking-wide">
                                {item.value}
                              </code>
                            </div>
                            <motion.button
                              whileHover={{ scale: 1.05 }}
                              whileTap={{ scale: 0.95 }}
                              onClick={async () => {
                                try {
                                  await navigator.clipboard.writeText(item.value);
                                } catch {}
                              }}
                              className="px-4 py-3 rounded-lg bg-primary hover:bg-primary/90 text-white font-medium transition-all duration-200 flex items-center gap-2"
                            >
                              <Copy className="w-4 h-4" />
                              <span className="hidden sm:inline">Copiar</span>
                            </motion.button>
                          </div>
                        </motion.div>
                      ))}
                    </motion.div>

                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.7 }}
                      className="flex flex-col sm:flex-row gap-3"
                    >
                      <motion.button
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        onClick={async () => {
                          try {
                            await navigator.clipboard.writeText(
                              `Código: ${lastCreated.codigo} | Protocolo: ${lastCreated.protocolo}`
                            );
                          } catch {}
                        }}
                        className="flex-1 px-4 py-3 rounded-lg border border-slate-600 hover:border-primary/50 text-slate-300 hover:text-white font-medium transition-all duration-200 flex items-center justify-center gap-2"
                      >
                        <Copy className="w-4 h-4" />
                        Copiar tudo
                      </motion.button>
                      <motion.button
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        onClick={() => setSuccessOpen(false)}
                        className="flex-1 px-4 py-3 rounded-lg bg-gradient-to-r from-primary to-primary/80 hover:from-primary hover:to-primary/70 text-white font-semibold transition-all duration-200"
                      >
                        Pronto, fechar
                      </motion.button>
                    </motion.div>
                  </div>
                </div>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </Layout>
  );
}

function TicketForm(props: {
  problemas?: {
    id: number;
    nome: string;
    prioridade: string;
    requer_internet: boolean;
  }[];
  unidades?: { id: number; nome: string; cidade: string }[];
  onSubmit: (payload: {
    nome: string;
    cargo: string;
    email: string;
    telefone: string;
    unidade: string;
    problema: string;
    internetItem?: string;
    descricao?: string;
    files?: File[];
  }) => void;
}) {
  const { onSubmit } = props;
  const listaProblemas = Array.isArray(props.problemas) ? props.problemas : [];
  const listaUnidades = Array.isArray(props.unidades) ? props.unidades : [];
  const [form, setForm] = useState({
    nome: "",
    cargo: "",
    email: "",
    telefone: "",
    unidade: "",
    problema: "",
    internetItem: "",
    descricao: "",
  });
  const [files, setFiles] = useState<File[]>([]);
  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    const must = [
      form.nome.trim(),
      form.cargo.trim(),
      form.email.trim(),
      form.telefone.trim(),
      form.unidade.trim(),
      form.problema.trim(),
      form.descricao.trim(),
    ];
    if (must.some((v) => !v)) {
      alert("Preencha todos os campos obrigatórios.");
      return;
    }
    if (selectedProblem?.requer_internet && !form.internetItem.trim()) {
      alert("Selecione o item de Internet.");
      return;
    }
    onSubmit({ ...form, files });
  };

  const selectedProblem = useMemo(
    () => listaProblemas.find((p) => p.nome === form.problema) || null,
    [listaProblemas, form.problema],
  );

  const formatTempo = (horas: number | null) => {
    if (!horas) return null;
    if (horas < 24) return `${horas}h`;
    const dias = horas / 24;
    return dias % 1 === 0 ? `${dias}d` : `${horas}h`;
  };

  const getPrioridadeColor = (prioridade: string) => {
    const colors: Record<string, string> = {
      Crítica: "text-red-600 dark:text-red-400",
      Alta: "text-orange-600 dark:text-orange-400",
      Normal: "text-blue-600 dark:text-blue-400",
      Baixa: "text-green-600 dark:text-green-400",
    };
    return colors[prioridade] || colors.Normal;
  };

  return (
    <form onSubmit={submit} className="grid gap-4">
      <div className="grid gap-2">
        <Label htmlFor="nome">Nome do solicitante</Label>
        <Input
          id="nome"
          value={form.nome}
          onChange={(e) => setForm({ ...form, nome: e.target.value })}
          required
        />
      </div>
      <div className="grid sm:grid-cols-2 gap-4">
        <div className="grid gap-2">
          <Label htmlFor="cargo">Cargo</Label>
          <Select
            value={form.cargo}
            onValueChange={(v) => setForm({ ...form, cargo: v })}
          >
            <SelectTrigger id="cargo">
              <SelectValue placeholder="Selecione" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="Coordenador">Coordenador</SelectItem>
              <SelectItem value="Funcionário">Funcionário</SelectItem>
              <SelectItem value="Gerente">Gerente</SelectItem>
              <SelectItem value="Gerente regional">Gerente regional</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>
      <div className="grid sm:grid-cols-2 gap-4">
        <div className="grid gap-2">
          <Label htmlFor="email">E-mail</Label>
          <Input
            id="email"
            type="email"
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
            required
          />
        </div>
        <div className="grid gap-2">
          <Label htmlFor="telefone">Telefone</Label>
          <Input
            id="telefone"
            inputMode="numeric"
            pattern="[0-9]*"
            placeholder="11987654321"
            value={form.telefone}
            onChange={(e) => setForm({ ...form, telefone: e.target.value })}
            required
          />
        </div>
      </div>
      <div className="grid sm:grid-cols-2 gap-4">
        <div className="grid gap-2">
          <Label>Selecione a unidade</Label>
          <Select
            value={form.unidade}
            onValueChange={(v) => setForm({ ...form, unidade: v })}
          >
            <SelectTrigger>
              <SelectValue placeholder="Selecione" />
            </SelectTrigger>
            <SelectContent>
              {listaUnidades.map((u) => (
                <SelectItem key={u.id} value={u.nome}>
                  {new RegExp(`(\\s*-\\s*${u.id})\\s*$`).test(u.nome)
                    ? u.nome
                    : `${u.nome} - ${u.id}`}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="grid gap-2">
          <Label>Problema Reportado</Label>
          <Select
            value={form.problema}
            onValueChange={(v) => setForm({ ...form, problema: v })}
          >
            <SelectTrigger>
              <SelectValue placeholder="Selecione" />
            </SelectTrigger>
            <SelectContent>
              {listaProblemas.map((p) => (
                <SelectItem key={p.id} value={p.nome}>
                  {p.nome}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {selectedProblem && (
        <div className="grid gap-2 p-3 rounded-lg bg-secondary/40 border border-secondary">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium">Prioridade:</span>
              <span
                className={`font-semibold text-sm ${getPrioridadeColor(selectedProblem.prioridade)}`}
              >
                {selectedProblem.prioridade}
              </span>
            </div>
            {selectedProblem.tempo_resolucao_horas && (
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium">Prazo máximo:</span>
                <span className="font-semibold text-sm">
                  {formatTempo(selectedProblem.tempo_resolucao_horas)}
                </span>
              </div>
            )}
          </div>
        </div>
      )}

      {selectedProblem?.requer_internet && (
        <div className="grid gap-2">
          <Label>Selecione o item de Internet</Label>
          <Select
            value={form.internetItem}
            onValueChange={(v) => setForm({ ...form, internetItem: v })}
          >
            <SelectTrigger>
              <SelectValue placeholder="Selecione" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="Antenas">Antenas</SelectItem>
              <SelectItem value="Cabo de rede">Cabo de rede</SelectItem>
              <SelectItem value="DVR">DVR</SelectItem>
              <SelectItem value="Roteador/Modem">Roteador/Modem</SelectItem>
              <SelectItem value="Switch">Switch</SelectItem>
              <SelectItem value="Wi-fi">Wi-fi</SelectItem>
            </SelectContent>
          </Select>
        </div>
      )}

      <div className="grid gap-2">
        <Label htmlFor="descricao">Descrição do problema</Label>
        <textarea
          id="descricao"
          className="min-h-[100px] rounded-md border border-input bg-background p-3 text-sm"
          placeholder="Descreva o que está acontecendo"
          value={form.descricao}
          onChange={(e) => setForm({ ...form, descricao: e.target.value })}
          required
        />
      </div>
      <div className="grid gap-2">
        <Label>Arquivos (opcional)</Label>
        <input
          type="file"
          multiple
          onChange={(e) => setFiles(Array.from(e.target.files || []))}
        />
      </div>
      <div className="flex items-center justify-end gap-3 pt-2">
        <Button type="submit">Salvar</Button>
      </div>
    </form>
  );
}
