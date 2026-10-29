import { createBrowserRouter, Link, RouterProvider } from "react-router";

import { RequireAdmin, RequireAuth } from "@/auth/guards";
import { AppLayout } from "@/components/layout/AppLayout";
import { buttonClass } from "@/components/ui/Button";
import { AccountPage } from "@/features/account/AccountPage";
import { CampusDetailPage } from "@/features/campuses/CampusDetailPage";
import { CampusesPage } from "@/features/campuses/CampusesPage";
import { EventDetailPage } from "@/features/events/EventDetailPage";
import { EventsPage } from "@/features/events/EventsPage";
import { ExamDetailPage } from "@/features/exams/ExamDetailPage";
import { ExamsPage } from "@/features/exams/ExamsPage";
import { StudentDetailPage } from "@/features/exams/StudentDetailPage";
import { HomePage } from "@/features/home/HomePage";
import { LoginPage } from "@/features/login/LoginPage";
import { NoteDetailPage } from "@/features/notes/NoteDetailPage";
import { NoteNewPage } from "@/features/notes/NoteNewPage";
import { NotesPage } from "@/features/notes/NotesPage";
import { InventoryPage } from "@/features/inventory/InventoryPage";
import { ShipmentDetailPage } from "@/features/shipments/ShipmentDetailPage";
import { ShipmentsPage } from "@/features/shipments/ShipmentsPage";
import { TodosPage } from "@/features/todos/TodosPage";
import { UsersPage } from "@/features/users/UsersPage";

function NotFound() {
  return (
    <div className="py-20 text-center">
      <p className="text-5xl font-extrabold text-stone-300">404</p>
      <p className="mt-2 font-semibold">Esta página no existe.</p>
      <Link to="/" className={buttonClass("secondary") + " mt-6"}>
        Volver al inicio
      </Link>
    </div>
  );
}

const router = createBrowserRouter([
  { path: "/login", element: <LoginPage /> },
  {
    element: <RequireAuth />,
    children: [
      {
        element: <AppLayout />,
        children: [
          { index: true, element: <HomePage /> },
          { path: "tareas", element: <TodosPage /> },
          { path: "notas", element: <NotesPage /> },
          { path: "notas/nueva", element: <NoteNewPage /> },
          { path: "notas/:noteId", element: <NoteDetailPage /> },
          { path: "correcciones", element: <ExamsPage /> },
          { path: "correcciones/:examId", element: <ExamDetailPage /> },
          { path: "alumnos/:studentId", element: <StudentDetailPage /> },
          { path: "eventos", element: <EventsPage /> },
          { path: "eventos/:eventId", element: <EventDetailPage /> },
          { path: "envios", element: <ShipmentsPage /> },
          { path: "envios/:shipmentId", element: <ShipmentDetailPage /> },
          { path: "material", element: <InventoryPage /> },
          { path: "campus", element: <CampusesPage /> },
          { path: "campus/:campusId", element: <CampusDetailPage /> },
          { path: "cuenta", element: <AccountPage /> },
          {
            element: <RequireAdmin />,
            children: [{ path: "usuarios", element: <UsersPage /> }],
          },
          { path: "*", element: <NotFound /> },
        ],
      },
    ],
  },
]);

export function App() {
  return <RouterProvider router={router} />;
}
