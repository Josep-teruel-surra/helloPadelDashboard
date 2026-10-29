import { useQueryClient } from "@tanstack/react-query";
import { useCallback } from "react";

/** Devuelve una función que invalida varias claves de caché a la vez. */
export function useInvalidate() {
  const queryClient = useQueryClient();
  return useCallback(
    (...keys: ReadonlyArray<readonly unknown[]>) =>
      Promise.all(keys.map((queryKey) => queryClient.invalidateQueries({ queryKey }))),
    [queryClient],
  );
}
