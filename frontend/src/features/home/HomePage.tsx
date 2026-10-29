import { useCurrentUser } from "@/auth/AuthContext";
import { PageHeader } from "@/components/ui/Layout";

// Provisional: los widgets (tiempo, tareas y notas) llegan en el paso de la home.
export function HomePage() {
  const user = useCurrentUser();
  return <PageHeader title={`Hola, ${user.full_name.split(" ")[0]}`} description="Resumen del día" />;
}
