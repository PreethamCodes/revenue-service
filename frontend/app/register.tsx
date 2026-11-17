"use client";
import { useState } from "react";
import type { FormEvent } from "react";
import type { RecordCard } from "./types";

type Lookup = {
  state: "idle" | "loading" | "empty" | "error" | "success";
  id?: string;
  message?: string;
  cards?: RecordCard[];
};

export default function Register() {
  const [value, setValue] = useState("");
  const [result, setResult] = useState<Lookup>({ state: "idle" });
  const busy = result.state === "loading";

  async function search(raw: string) {
    const id = raw.trim().toUpperCase();
    setValue(id);
    if (!/^MHSTU[0-9]{4}$/.test(id)) {
      setResult({
        state: "error",
        message: "Enter a student ID in the format MHSTU0001.",
      });
      return;
    }
    setResult({ state: "loading", id });
    try {
      const response = await fetch("/api/lookup?id=" + encodeURIComponent(id), {
        cache: "no-store",
      });
      const data = await response.json();
      if (!response.ok) {
        setResult({
          state: response.status === 404 ? "empty" : "error",
          id,
          message: data.message,
        });
      } else {
        setResult({ state: "success", id, cards: data.cards });
      }
    } catch {
      setResult({
        state: "error",
        id,
        message: "The register could not be reached. Try the lookup again.",
      });
    }
  }
  function submit(event: FormEvent) {
    event.preventDefault();
    void search(value);
  }

  return (
    <>
      <div className="desk">
        <section className="panel">
          <h2>Certificate lookup</h2>
          <form onSubmit={submit}>
            <label htmlFor="student">Student ID</label>
            <div className="searchline">
              <input
                id="student"
                value={value}
                onChange={(e) => setValue(e.target.value)}
                placeholder="MHSTU0001"
                autoComplete="off"
                spellCheck={false}
                maxLength={24}
                disabled={busy}
              />
              <button type="submit" disabled={busy}>
                {busy ? "Searching…" : "Find records"}{" "}
                <span aria-hidden="true">→</span>
              </button>
            </div>
          </form>
          <p className="hint">
            Both certificate types are retrieved in one request.
          </p>
        </section>
        <aside>
          <h2>Demo files</h2>
          <p>Open a seeded student record.</p>
          {[
            ["Standard record", "MHSTU0001"],
            ["Expired certificates", "MHSTU0003"],
          ].map(([label, id]) => (
            <button
              type="button"
              disabled={busy}
              key={id}
              onClick={() => void search(id)}
            >
              <span>{label}</span>
              <code>{id} ↗</code>
            </button>
          ))}
        </aside>
      </div>
      <section className="results" aria-label="Lookup results" aria-busy={busy}>
        <div className="resulthead">
          <h2>Record details</h2>
          {result.id && <code>{result.id}</code>}
        </div>
        <div
          aria-live="polite"
          role="status"
          className={result.state === "error" ? "notice error" : "notice"}
        >
          {result.state === "idle" &&
            "Search by student ID or open a demo file to view department records."}
          {busy && "Retrieving records from the department…"}
          {result.state === "empty" && (
            <>
              <strong>No records found. </strong>
              {result.message}
            </>
          )}
          {result.state === "error" && result.message}
          {result.state === "success" && "Department records retrieved."}
        </div>
        <div className="cards">
          {result.cards?.map((card) => (
            <article key={card.title}>
              <div className="cardhead">
                <h3>{card.title}</h3>
                <span className={"status " + card.tone}>{card.status}</span>
              </div>
              <dl>
                {card.fields.map(([name, val]) => (
                  <div key={name}>
                    <dt>{name}</dt>
                    <dd>{val}</dd>
                  </div>
                ))}
              </dl>
            </article>
          ))}
        </div>
      </section>
    </>
  );
}
