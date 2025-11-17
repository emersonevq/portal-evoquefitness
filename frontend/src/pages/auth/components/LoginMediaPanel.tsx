import { useEffect, useRef, useState } from "react";
import useEmblaCarousel from "embla-carousel-react";
import { apiFetch } from "@/lib/api";

type MediaKind = "image" | "video";

interface MediaItem {
  id: string | number;
  type: MediaKind;
  url?: string;
  mime?: string;
}

async function fetchLoginMedia(signal?: AbortSignal): Promise<MediaItem[]> {
  try {
    const res = await apiFetch("/login-media", { signal });
    if (!res.ok) return [];
    const data = await res.json();
    return Array.isArray(data) ? data : [];
  } catch {
    return [];
  }
}

export default function LoginMediaPanel() {
  const defaultItems: MediaItem[] = [
    {
      id: "default-1",
      type: "image",
      url: "https://cdn.builder.io/api/v1/image/assets%2Ffebea1b69437410ebd88e454001ca510%2Fe38b6c90873e4ea48f163db39b62fff9?format=webp&width=1600",
    },
    {
      id: "default-2",
      type: "image",
      url: "https://cdn.builder.io/api/v1/image/assets%2Ffebea1b69437410ebd88e454001ca510%2F3a4a4f300e384651b805810074ea77d3?format=webp&width=1600",
    },
  ];

  const [items, setItems] = useState<MediaItem[]>(defaultItems);
  const [emblaRef, emblaApi] = useEmblaCarousel({
    loop: true,
    align: "center",
    skipSnaps: false,
  });

  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const videoListenersRef = useRef<Map<number, () => void>>(new Map());

  useEffect(() => {
    const controller = new AbortController();
    fetchLoginMedia(controller.signal).then((list) => {
      if (list.length > 0) setItems(list);
    });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    if (!emblaApi) return;

    const onSelect = () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);

      const idx = emblaApi.selectedIndex;
      const item = items[idx];

      // Clean up old listeners
      videoListenersRef.current.forEach((cleanup) => cleanup());
      videoListenersRef.current.clear();

      if (item?.type === "video") {
        const slides = emblaApi.containerNode()?.querySelectorAll(".embla__slide");
        const video = slides?.[idx]?.querySelector("video") as HTMLVideoElement | null;

        if (video) {
          const handleEnd = () => emblaApi.scrollNext();
          video.addEventListener("ended", handleEnd, { once: true });
          videoListenersRef.current.set(idx, () =>
            video.removeEventListener("ended", handleEnd)
          );
        }
      } else {
        timeoutRef.current = setTimeout(() => emblaApi.scrollNext(), 6000);
      }
    };

    onSelect();
    const unsub = emblaApi.on("select", onSelect);

    return () => {
      unsub();
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      videoListenersRef.current.forEach((cleanup) => cleanup());
    };
  }, [emblaApi, items]);

  return (
    <div className="relative overflow-hidden rounded-2xl mx-auto w-[360px] h-[360px] sm:w-[460px] sm:h-[460px] md:w-[520px] md:h-[520px] lg:w-[560px] lg:h-[560px] xl:w-[640px] xl:h-[640px]">
      <div className="absolute inset-0 brand-gradient opacity-70" />
      <div className="relative h-full embla" ref={emblaRef}>
        <div className="embla__container flex h-full">
          {items.map((item) => (
            <div
              key={item.id}
              className="embla__slide min-w-0 flex-[0_0_100%] h-full"
            >
              {item.type === "image" ? (
                <img
                  src={item.url}
                  alt="Media"
                  className="w-full h-full object-cover"
                />
              ) : (
                <video
                  className="w-full h-full object-cover"
                  autoPlay
                  muted
                  playsInline
                  controls={false}
                >
                  <source src={item.url} type={item.mime || "video/mp4"} />
                </video>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
