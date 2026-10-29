import {
  Cloud,
  CloudDrizzle,
  CloudFog,
  CloudLightning,
  CloudMoon,
  CloudRain,
  CloudSnow,
  CloudSun,
  Droplets,
  MapPin,
  Moon,
  RotateCw,
  Sun,
  TriangleAlert,
  Wind,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

import { useWeather } from "@/api/queries";
import type { Weather, WeatherIcon as IconName } from "@/api/types";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Layout";
import { Spinner } from "@/components/ui/Spinner";
import { cn } from "@/lib/cn";
import { parseLocalDate } from "@/lib/format";
import { useGeolocation } from "./useGeolocation";

const ICONS: Record<IconName, LucideIcon> = {
  clear: Sun,
  "partly-cloudy": CloudSun,
  cloudy: Cloud,
  fog: CloudFog,
  drizzle: CloudDrizzle,
  rain: CloudRain,
  snow: CloudSnow,
  storm: CloudLightning,
};

const NIGHT_ICONS: Partial<Record<IconName, LucideIcon>> = { clear: Moon, "partly-cloudy": CloudMoon };

function WeatherIcon({ icon, isDay = true, className }: { icon: IconName; isDay?: boolean; className?: string }) {
  const Icon = (!isDay && NIGHT_ICONS[icon]) || ICONS[icon];
  return <Icon className={className} aria-hidden />;
}

const round = (value: number | null | undefined) => (value == null ? "–" : Math.round(value));

/** Hora local de Open-Meteo ("2026-10-29T13:00:00") → "13:00", sin conversión de zona. */
const hourLabel = (time: string) => time.slice(11, 16);

const weekday = (isoDate: string) =>
  parseLocalDate(isoDate).toLocaleDateString("es-ES", { weekday: "short" }).replace(".", "");

/** Avisos útiles para decidir sobre las pistas exteriores. */
function courtWarnings(weather: Weather): string[] {
  const warnings: string[] = [];
  const nextHours = weather.hourly.slice(1, 4);
  if (["rain", "drizzle", "storm", "snow"].includes(weather.current.icon)) {
    warnings.push("Está lloviendo: revisa las reservas de pistas exteriores.");
  } else if (nextHours.some((h) => (h.precipitation_probability ?? 0) >= 50)) {
    warnings.push("Probable lluvia en las próximas 3 horas.");
  }
  if ((weather.current.wind_gusts ?? 0) >= 40) {
    warnings.push(`Rachas de viento de ${round(weather.current.wind_gusts)} km/h.`);
  }
  return warnings;
}

export function WeatherWidget({ className }: { className?: string }) {
  const geo = useGeolocation();
  const coords = geo.status === "granted" ? geo.coords : null;
  const weather = useWeather(coords, geo.status !== "pending");

  const locationLabel = weather.data?.location.name ?? "Tu ubicación";

  return (
    <Card
      className={className}
      title="Tiempo"
      icon={<Sun className="size-4" aria-hidden />}
      actions={
        weather.data && (
          <span className="flex items-center gap-1 text-xs text-stone-500">
            <MapPin className="size-3.5" aria-hidden />
            {locationLabel}
          </span>
        )
      }
    >
      {geo.status === "pending" || weather.isPending ? (
        <Spinner label={geo.status === "pending" ? "Buscando tu ubicación…" : "Cargando el tiempo…"} />
      ) : weather.isError ? (
        <div className="flex flex-col items-center gap-3 py-8 text-center text-sm text-stone-500">
          <p>No se ha podido cargar el tiempo.</p>
          <Button variant="secondary" size="sm" onClick={() => void weather.refetch()}>
            <RotateCw className="size-4" aria-hidden />
            Reintentar
          </Button>
        </div>
      ) : (
        <WeatherDetails weather={weather.data} />
      )}
    </Card>
  );
}

function WeatherDetails({ weather }: { weather: Weather }) {
  const { current } = weather;
  const warnings = courtWarnings(weather);

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-4">
        <WeatherIcon
          icon={current.icon}
          isDay={current.is_day}
          className="size-14 shrink-0 text-amber-500"
        />
        <div className="min-w-0">
          <p className="text-4xl font-extrabold tracking-tight">{round(current.temperature)}°</p>
          <p className="text-sm font-medium text-stone-600">{current.description}</p>
        </div>
      </div>

      <dl className="flex flex-wrap gap-1.5 text-xs text-stone-600">
        <div className="flex items-center gap-1 rounded-md bg-stone-100 px-2 py-1">
          <dt>Sensación</dt>
          <dd className="font-semibold">{round(current.apparent_temperature)}°</dd>
        </div>
        <div className="flex items-center gap-1 rounded-md bg-stone-100 px-2 py-1">
          <dt>
            <Wind className="size-3.5" aria-label="Viento" />
          </dt>
          <dd>
            <span className="font-semibold">{round(current.wind_speed)} km/h</span>
            {current.wind_gusts != null && ` · rachas ${round(current.wind_gusts)}`}
          </dd>
        </div>
        <div className="flex items-center gap-1 rounded-md bg-stone-100 px-2 py-1">
          <dt>
            <Droplets className="size-3.5" aria-label="Humedad" />
          </dt>
          <dd className="font-semibold">{round(current.humidity)}%</dd>
        </div>
      </dl>

      {warnings.length > 0 && (
        <ul className="space-y-1 rounded-lg bg-amber-50 px-3 py-2 text-xs font-medium text-amber-900">
          {warnings.map((warning) => (
            <li key={warning} className="flex items-start gap-1.5">
              <TriangleAlert className="mt-px size-3.5 shrink-0" aria-hidden />
              {warning}
            </li>
          ))}
        </ul>
      )}

      {/* Próximas horas (la primera es la hora en curso) */}
      <ol className="-mx-1 flex gap-1 overflow-x-auto pb-1" aria-label="Próximas horas">
        {weather.hourly.slice(1, 7).map((hour) => (
          <li key={hour.time} className="flex min-w-11 flex-1 flex-col items-center gap-1 rounded-lg py-1.5">
            <span className="text-xs text-stone-500">{hourLabel(hour.time)}</span>
            <WeatherIcon icon={hour.icon} className="size-5 text-stone-600" />
            <span className="text-sm font-semibold">{round(hour.temperature)}°</span>
            <span
              className={cn(
                "text-[11px]",
                (hour.precipitation_probability ?? 0) >= 50 ? "font-semibold text-sky-700" : "text-stone-400",
              )}
            >
              {round(hour.precipitation_probability)}%
            </span>
          </li>
        ))}
      </ol>

      {/* Próximos días (sin hoy) */}
      <ul className="divide-y divide-stone-100 border-t border-stone-100" aria-label="Próximos días">
        {weather.daily.slice(1).map((day) => (
          <li key={day.date} className="flex items-center gap-3 py-2 text-sm">
            <span className="w-10 font-medium capitalize">{weekday(day.date)}</span>
            <WeatherIcon icon={day.icon} className="size-5 text-stone-600" />
            <span className="min-w-0 flex-1 truncate text-stone-500">{day.description}</span>
            <span className="text-xs text-sky-700">{round(day.precipitation_probability_max)}%</span>
            <span className="w-16 text-right tabular-nums">
              <span className="text-stone-400">{round(day.temperature_min)}°</span>{" "}
              <span className="font-semibold">{round(day.temperature_max)}°</span>
            </span>
          </li>
        ))}
      </ul>

      {(weather.stale || weather.location.is_default) && (
        <p className="text-xs text-stone-400">
          {weather.stale && "Open-Meteo no responde: mostramos el último dato guardado. "}
          {weather.location.is_default &&
            "Sin permiso de ubicación: mostramos el tiempo de Barcelona."}
        </p>
      )}
    </div>
  );
}
