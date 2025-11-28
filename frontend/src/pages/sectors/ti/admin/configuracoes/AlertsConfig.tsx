import { useEffect, useState, useRef } from "react";
import { apiFetch } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { X } from "lucide-react";

type MediaItem = { id: number | string; url?: string; type?: string };

export default function AlertsConfig() {
  const [title, setTitle] = useState("");
  const [message, setMessage] = useState("");
  const [severity, setSeverity] = useState("info");
  const [link, setLink] = useState("");
  const [startAt, setStartAt] = useState<string | null>(null);
  const [endAt, setEndAt] = useState<string | null>(null);
  const [mediaId, setMediaId] = useState<number | null>(null);
  const [mediaList, setMediaList] = useState<MediaItem[]>([]);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [imagemFile, setImagemFile] = useState<File | null>(null);
  const [imagemPreview, setImagemPreview] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const loadMedia = async () => {
    const res = await apiFetch("/login-media");
    if (!res.ok) return;
    const data = await res.json();
    setMediaList(Array.isArray(data) ? data : []);
  };
  const loadAlerts = async () => {
    const res = await apiFetch("/alerts");
    if (!res.ok) return;
    const data = await res.json();
    setAlerts(Array.isArray(data) ? data : []);
  };

  const handleImagemChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setImagemFile(file);
      const reader = new FileReader();
      reader.onload = (event) => {
        setImagemPreview(event.target?.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const limparImagem = () => {
    setImagemFile(null);
    setImagemPreview(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  useEffect(() => {
    loadMedia();
    loadAlerts();
  }, []);

  const create = async () => {
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append("title", title);
      formData.append("message", message);
      formData.append("severity", severity);
      if (link) formData.append("link", link);
      if (mediaId) formData.append("media_id", String(mediaId));
      if (startAt) formData.append("start_at", startAt);
      if (endAt) formData.append("end_at", endAt);
      formData.append("ativo", "true");

      if (imagemFile) {
        formData.append("imagem", imagemFile);
      }

      const res = await apiFetch("/alerts", {
        method: "POST",
        body: formData,
      });
      if (!res.ok) {
        alert("Falha ao criar alerta");
      } else {
        setTitle("");
        setMessage("");
        setLink("");
        setMediaId(null);
        limparImagem();
        await loadAlerts();
      }
    } finally {
      setLoading(false);
    }
  };

  const remove = async (id: number) => {
    if (!confirm("Remover alerta?")) return;
    const res = await apiFetch(`/alerts/${id}`, { method: "DELETE" });
    if (!res.ok) {
      alert("Falha ao remover");
      return;
    }
    await loadAlerts();
  };

  return (
    <div className="card-surface rounded-xl p-4 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <div className="font-semibold">Alertas do Sistema</div>
          <p className="text-sm text-muted-foreground">
            Crie mensagens que serão exibidas na página inicial para todos os
            usuários.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-3">
        <Input
          placeholder="Título"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
        />
        <Input
          placeholder="Mensagem"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
        />
        <div className="flex gap-2">
          <select
            className="rounded-md bg-background border px-3 py-2"
            value={severity}
            onChange={(e) => setSeverity(e.target.value)}
          >
            <option value="info">Info</option>
            <option value="warning">Aviso</option>
            <option value="danger">Crítico</option>
          </select>
          <Input
            placeholder="Link (opcional)"
            value={link}
            onChange={(e) => setLink(e.target.value)}
          />
        </div>
        <div className="flex gap-2">
          <Input
            type="datetime-local"
            value={startAt || ""}
            onChange={(e) => setStartAt(e.target.value)}
          />
          <Input
            type="datetime-local"
            value={endAt || ""}
            onChange={(e) => setEndAt(e.target.value)}
          />
        </div>
        <div>
          <div className="text-sm text-muted-foreground mb-1">
            Mídia associada (opcional)
          </div>
          <select
            className="rounded-md bg-background border px-3 py-2 w-full"
            value={mediaId ?? ""}
            onChange={(e) =>
              setMediaId(e.target.value ? Number(e.target.value) : null)
            }
          >
            <option value="">Nenhuma</option>
            {mediaList.map((m) => (
              <option key={m.id} value={m.id}>
                {m.id} — {m.type}
              </option>
            ))}
          </select>
        </div>
        <div>
          <div className="text-sm text-muted-foreground mb-2">
            Imagem do alerta (opcional)
          </div>
          <div className="flex items-center gap-2">
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={handleImagemChange}
              className="hidden"
            />
            <Button
              type="button"
              variant="outline"
              onClick={() => fileInputRef.current?.click()}
            >
              Escolher imagem
            </Button>
            {imagemFile && (
              <span className="text-sm text-muted-foreground">
                {imagemFile.name}
              </span>
            )}
          </div>
          {imagemPreview && (
            <div className="mt-3 relative inline-block">
              <img
                src={imagemPreview}
                alt="Preview"
                className="max-w-xs max-h-40 rounded-md border"
              />
              <button
                onClick={limparImagem}
                className="absolute top-1 right-1 bg-destructive text-destructive-foreground rounded-full p-1 hover:opacity-80"
              >
                <X size={16} />
              </button>
            </div>
          )}
        </div>
        <div className="flex items-center gap-2">
          <Button onClick={create} disabled={loading}>
            {loading ? "Salvando..." : "Criar alerta"}
          </Button>
        </div>
      </div>

      <div>
        <h3 className="font-semibold mt-4 mb-2">Alertas existentes</h3>
        <div className="grid gap-4">
          {alerts.map((a) => (
            <div
              key={a.id}
              className="border rounded-md p-3 flex items-start justify-between gap-3"
            >
              <div className="flex-1">
                <div className="font-semibold">{a.title || "(sem título)"}</div>
                <div className="text-sm text-muted-foreground">{a.message}</div>
                <div className="text-xs text-muted-foreground mt-1">
                  {a.severity} — {a.start_at || ""} → {a.end_at || ""}
                </div>
                {a.imagem_blob && (
                  <div className="mt-2">
                    <img
                      src={`data:${a.imagem_mime_type || "image/jpeg"};base64,${a.imagem_blob}`}
                      alt="Alerta"
                      className="max-w-xs max-h-32 rounded-md border"
                    />
                  </div>
                )}
              </div>
              <div>
                <button
                  onClick={() => remove(a.id)}
                  className="text-xs px-2 py-1 rounded-md bg-destructive text-destructive-foreground whitespace-nowrap"
                >
                  Remover
                </button>
              </div>
            </div>
          ))}
          {alerts.length === 0 && (
            <div className="text-sm text-muted-foreground">Nenhum alerta</div>
          )}
        </div>
      </div>
    </div>
  );
}
