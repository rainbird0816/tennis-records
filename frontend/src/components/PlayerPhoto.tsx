import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import Flag from "./Flag";

/** Wikidata 엔터티 → 대표 이미지(P18) → Wikimedia Commons 파일 URL. */
async function fetchPhoto(qid: string): Promise<string | null> {
  const url = `https://www.wikidata.org/w/api.php?action=wbgetclaims&entity=${qid}&property=P18&format=json&origin=*`;
  const res = await fetch(url);
  if (!res.ok) return null;
  const j = await res.json();
  const file = j?.claims?.P18?.[0]?.mainsnak?.datavalue?.value;
  if (!file || typeof file !== "string") return null;
  return `https://commons.wikimedia.org/wiki/Special:FilePath/${encodeURIComponent(file)}?width=320`;
}

interface Props {
  wikidataId: string | null;
  name: string;
  ioc: string | null;
}

/** 선수 사진 — Wikidata 사진이 있으면 표시, 없으면 이니셜 아바타 + 국기. */
export default function PlayerPhoto({ wikidataId, name, ioc }: Props) {
  const [errored, setErrored] = useState(false);
  const { data: url } = useQuery({
    queryKey: ["photo", wikidataId],
    queryFn: () => fetchPhoto(wikidataId as string),
    enabled: !!wikidataId,
    staleTime: Infinity,
    retry: false,
  });

  const initials = name
    .split(/\s+/)
    .map((w) => w[0])
    .filter(Boolean)
    .slice(0, 2)
    .join("")
    .toUpperCase();

  if (url && !errored) {
    return (
      <img
        src={url}
        alt={name}
        onError={() => setErrored(true)}
        loading="lazy"
        className="h-28 w-24 rounded-lg object-cover border bg-neutral-100"
      />
    );
  }

  // 폴백: 코트그린 이니셜 아바타 + 국기 뱃지
  return (
    <div className="relative h-28 w-24 rounded-lg border bg-court/10 flex items-center justify-center">
      <span className="text-2xl font-bold text-court/70">{initials}</span>
      <span className="absolute bottom-1 right-1">
        <Flag ioc={ioc} className="h-3 w-[18px] rounded-[2px] object-cover border border-white" />
      </span>
    </div>
  );
}
