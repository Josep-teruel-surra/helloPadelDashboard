import type { Address } from "@/api/types";
import { countryName } from "@/lib/countries";

export function AddressBlock({ address }: { address: Address | null }) {
  if (!address) return <p className="text-sm text-stone-400">Sin dirección de envío.</p>;
  const cityLine = [address.postal_code, address.city, address.region].filter(Boolean).join(" ");
  const lines = [
    address.recipient,
    address.line1,
    address.line2,
    cityLine,
    address.country_code && countryName(address.country_code),
  ].filter(Boolean);
  return (
    <address className="text-sm leading-relaxed text-stone-700 not-italic">
      {lines.map((line) => (
        <span key={line} className="block">
          {line}
        </span>
      ))}
    </address>
  );
}
