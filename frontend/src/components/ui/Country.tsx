import { COUNTRY_OPTIONS, countryName, flag } from "@/lib/countries";
import { inputClass } from "./Field";

export function CountryFlag({ code, className }: { code: string; className?: string }) {
  return (
    <span role="img" aria-label={countryName(code)} title={countryName(code)} className={className}>
      {flag(code)}
    </span>
  );
}

export function CountrySelect({
  id,
  value,
  onChange,
  required,
  emptyLabel = "Elige un país",
}: {
  id: string;
  value: string;
  onChange: (code: string) => void;
  required?: boolean;
  emptyLabel?: string;
}) {
  return (
    <select
      id={id}
      required={required}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className={inputClass}
    >
      <option value="">{emptyLabel}</option>
      {COUNTRY_OPTIONS.map(({ code, name }) => (
        <option key={code} value={code}>
          {flag(code)} {name}
        </option>
      ))}
    </select>
  );
}
