import { createBrowserRouter, Link, RouterProvider } from "react-router";

import { RequireAdmin, RequireAuth } from "@/auth/guards";
import { AppLayout } from "@/components/layout/AppLayout";
import { buttonClass } from "@/components/ui/Button";
import { AccountPage } from "@/features/account/AccountPage";
import { HomePage } from "@/features/home/HomePage";
import { LoginPage } from "@/features/login/LoginPage";
import { NoteDetailPage } from "@/features/notes/NoteDetailPage";
import { NoteNewPage } from "@/features/notes/NoteNewPage";
import { NotesPage } from "@/features/notes/NotesPage";
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
