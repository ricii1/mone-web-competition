"use client";

import { useEffect, useState } from "react";
import { api } from "./api";

/** Loads the class title for navigation labels; stays null if it cannot be fetched. */
export function useClassTitle(classId: string): string | null {
  const [title, setTitle] = useState<string | null>(null);
  useEffect(() => {
    let active = true;
    api
      .getClass(classId)
      .then((c) => active && setTitle(c.title))
      .catch(() => {});
    return () => {
      active = false;
    };
  }, [classId]);
  return title;
}
