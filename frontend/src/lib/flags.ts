// IOC(또는 데이터에 섞여 있는 ISO3) 국가코드 → ISO 3166-1 alpha-2 → 국기 이모지.
// 매핑되지 않는 역사적 코드(URS/YUG/TCH 등)는 null → 국기 없이 코드만 표기.

const IOC_TO_ISO2: Record<string, string> = {
  AFG: "AF", ALB: "AL", ALG: "DZ", AND: "AD", ANG: "AO", ANT: "AG", ARG: "AR",
  ARM: "AM", ARU: "AW", ASA: "AS", AUS: "AU", AUT: "AT", AZE: "AZ", BAH: "BS",
  BAN: "BD", BAR: "BB", BDI: "BI", BEL: "BE", BEN: "BJ", BER: "BM", BHR: "BH",
  BIH: "BA", BIZ: "BZ", BLR: "BY", BOL: "BO", BOT: "BW", BRA: "BR", BRN: "BH",
  BRU: "BN", BUL: "BG", BUR: "BF", CAF: "CF", CAM: "KH", CAN: "CA", CAY: "KY",
  CGO: "CG", CHA: "TD", CHI: "CL", CHN: "CN", CIV: "CI", CMR: "CM", COD: "CD",
  COK: "CK", COL: "CO", COM: "KM", CPV: "CV", CRC: "CR", CRO: "HR", CUB: "CU",
  CUW: "CW", CYP: "CY", CZE: "CZ", DEN: "DK", DJI: "DJ", DOM: "DO", ECU: "EC",
  EGY: "EG", ERI: "ER", ESA: "SV", ESP: "ES", EST: "EE", ETH: "ET", FIJ: "FJ",
  FIN: "FI", FRA: "FR", GAB: "GA", GAM: "GM", GBR: "GB", GEO: "GE", GER: "DE",
  GHA: "GH", GRE: "GR", GRN: "GD", GUA: "GT", GUI: "GN", GUM: "GU", GUY: "GY",
  HAI: "HT", HKG: "HK", HON: "HN", HUN: "HU", INA: "ID", IND: "IN", IRI: "IR",
  IRL: "IE", IRQ: "IQ", ISL: "IS", ISR: "IL", ISV: "VI", ITA: "IT", IVB: "VG",
  JAM: "JM", JOR: "JO", JPN: "JP", KAZ: "KZ", KEN: "KE", KGZ: "KG", KNA: "KN",
  KOR: "KR", KOS: "XK", KSA: "SA", KUW: "KW", LAO: "LA", LAT: "LV", LBA: "LY",
  LBN: "LB", LBR: "LR", LCA: "LC", LEB: "LB", LES: "LS", LIB: "LB", LIE: "LI",
  LTU: "LT", LUX: "LU", MAC: "MO", MAD: "MG", MAR: "MA", MAS: "MY", MAW: "MW",
  MDA: "MD", MDV: "MV", MEX: "MX", MGL: "MN", MHL: "MH", MKD: "MK", MLI: "ML",
  MLT: "MT", MNE: "ME", MON: "MC", MOZ: "MZ", MRI: "MU", MTN: "MR", MYA: "MM",
  NAM: "NA", NCA: "NI", NED: "NL", NEP: "NP", NGR: "NG", NIG: "NE", NOR: "NO",
  NZL: "NZ", OMA: "OM", PAK: "PK", PAN: "PA", PAR: "PY", PER: "PE", PHI: "PH",
  PLE: "PS", PLW: "PW", PNG: "PG", POL: "PL", POR: "PT", PRK: "KP", PUR: "PR",
  QAT: "QA", ROU: "RO", RSA: "ZA", RUS: "RU", RWA: "RW", SAM: "WS", SEN: "SN",
  SEY: "SC", SGP: "SG", SIN: "SG", SLE: "SL", SLO: "SI", SMR: "SM", SOL: "SB",
  SRB: "RS", SRI: "LK", SUD: "SD", SUI: "CH", SUR: "SR", SVK: "SK", SWE: "SE",
  SWZ: "SZ", SYR: "SY", TAN: "TZ", TGO: "TG", THA: "TH", TJK: "TJ", TKM: "TM",
  TLS: "TL", TOG: "TG", TPE: "TW", TRI: "TT", TTO: "TT", TUN: "TN", TUR: "TR",
  UAE: "AE", UGA: "UG", UKR: "UA", URU: "UY", USA: "US", UZB: "UZ", VAN: "VU",
  VEN: "VE", VIE: "VN", VIN: "VC", VIR: "VI", YEM: "YE", ZAM: "ZM", ZIM: "ZW",
  // 데이터에 섞여 들어온 ISO3 변형
  BGR: "BG", BHS: "BS", BRB: "BB", CHL: "CL", CRI: "CR", DEU: "DE", HRV: "HR",
  KWT: "KW", LVA: "LV", MDG: "MG", MNG: "MN", MRT: "MR", MUS: "MU", NGA: "NG",
  NLD: "NL", NPL: "NP", PHL: "PH", PRI: "PR", PRY: "PY", SCG: "RS", SVN: "SI",
  TWN: "TW", ZMB: "ZM", ZWE: "ZW",
};

/** IOC/ISO3 코드 → ISO 3166-1 alpha-2 소문자 (flagcdn URL용). 매핑 불가 시 null. */
export function iocToIso2(ioc: string | null | undefined): string | null {
  if (!ioc) return null;
  const iso2 = IOC_TO_ISO2[ioc.trim().toUpperCase()];
  return iso2 ? iso2.toLowerCase() : null;
}

/** IOC/ISO3 코드 → 국기 이모지 (Windows 미렌더링 — 이미지 Flag 컴포넌트 권장). */
export function flagEmoji(ioc: string | null | undefined): string {
  const iso2 = iocToIso2(ioc);
  if (!iso2) return "";
  return String.fromCodePoint(
    ...[...iso2.toUpperCase()].map((ch) => 0x1f1e6 + (ch.charCodeAt(0) - 65)),
  );
}
