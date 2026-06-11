import { iocToIso2 } from "../lib/flags";

interface Props {
  ioc: string | null | undefined;
  className?: string;
}

/** 국기 이미지 (flagcdn). Windows 등 이모지 미지원 환경에서도 일관 렌더.
 *  매핑 불가 코드는 렌더하지 않음(상위에서 IOC 텍스트로 대체). */
export default function Flag({ ioc, className }: Props) {
  const iso2 = iocToIso2(ioc);
  if (!iso2) return null;
  return (
    <img
      src={`https://flagcdn.com/${iso2}.svg`}
      alt={ioc ?? ""}
      title={ioc ?? ""}
      loading="lazy"
      className={className ?? "inline-block h-3 w-[18px] rounded-[2px] object-cover align-[-1px]"}
    />
  );
}
