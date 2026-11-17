export type RecordCard = {
  title: string;
  status: string;
  tone: "ok" | "attention" | "neutral";
  fields: [string, string][];
};
