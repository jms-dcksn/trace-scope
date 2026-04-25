import Database from "better-sqlite3";
import path from "node:path";

declare global {
  // eslint-disable-next-line no-var
  var __evalDb: Database.Database | undefined;
}

const DB_PATH = path.resolve(process.cwd(), "..", "evals.db");

export function db(): Database.Database {
  if (!global.__evalDb) {
    const conn = new Database(DB_PATH);
    conn.pragma("foreign_keys = ON");
    conn.pragma("journal_mode = WAL");
    global.__evalDb = conn;
  }
  return global.__evalDb;
}

export function nowIso(): string {
  return new Date().toISOString().replace(/\.\d{3}Z$/, "+00:00");
}
