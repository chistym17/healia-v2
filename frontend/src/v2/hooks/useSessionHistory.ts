import { useCallback, useEffect, useState } from "react";
import { deleteSession, getSession, listSessions } from "@/v2/lib/sessionsApi";
import type { SessionSummary, StoredSessionResults, SessionRecord } from "@/v2/types/session";

export function useSessionHistory(limit = 50) {
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const reload = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const rows = await listSessions(limit);
      setSessions(rows);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load history");
    } finally {
      setIsLoading(false);
    }
  }, [limit]);

  const removeSession = useCallback(async (sessionId: string) => {
    setDeletingId(sessionId);
    try {
      await deleteSession(sessionId);
      setSessions((prev) => prev.filter((s) => s.id !== sessionId));
    } finally {
      setDeletingId(null);
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  return { sessions, isLoading, error, reload, removeSession, deletingId };
}

export function useSessionDetail(sessionId: string | undefined) {
  const [session, setSession] = useState<SessionRecord | null>(null);
  const [results, setResults] = useState<StoredSessionResults | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    if (!sessionId) return;
    setIsLoading(true);
    setError(null);
    try {
      const data = await getSession(sessionId);
      setSession(data.session);
      setResults(data.results);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load consultation");
    } finally {
      setIsLoading(false);
    }
  }, [sessionId]);

  useEffect(() => {
    void reload();
  }, [reload]);

  return { session, results, isLoading, error, reload };
}
