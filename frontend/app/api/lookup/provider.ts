import { XMLParser, XMLValidator } from "fast-xml-parser";
import { z } from "zod";
import { randomUUID } from "node:crypto";
import type { RecordCard } from "../../types";
import { call, setting } from "./transport";

const certificate = z.object({
  ProviderRecordReference: z.string().min(1),
  CertificateStatus: z.enum(["VALID", "EXPIRED", "REVOKED"]),
  IssueDate: z.iso.date(),
  ExpiryDate: z.iso.date(),
});
const response = z.object({
  StudentID: z.string(),
  RequestReference: z.string(),
  IncomeCertificate: certificate
    .extend({ AnnualIncomeINR: z.string().regex(/^\d+(\.\d+)?$/) })
    .optional(),
  CasteCertificate: certificate
    .extend({ Category: z.string().min(1) })
    .optional(),
});

export async function lookup(id: string): Promise<RecordCard[]> {
  const reference = randomUUID();
  const credentials = Buffer.from(
    setting("REVENUE_USER") + ":" + setting("REVENUE_PASSWORD"),
  ).toString("base64");
  const reply = await call("/soap/v1", {
    method: "POST",
    headers: {
      Authorization: "Basic " + credentials,
      "Content-Type":
        'application/soap+xml; charset=utf-8; action="urn:mahasetu:revenue:v1/GetStudentCertificates"',
    },
    body: `<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope" xmlns:r="urn:mahasetu:revenue:v1"><s:Body><r:GetStudentCertificates><r:StudentID>${id}</r:StudentID><r:RequestReference>${reference}</r:RequestReference></r:GetStudentCertificates></s:Body></s:Envelope>`,
  });
  const xml = await reply.text();
  if (xml.includes("<!DOCTYPE") || XMLValidator.validate(xml) !== true)
    throw new Error("Invalid certificate XML");
  const envelope = new XMLParser({
    removeNSPrefix: true,
    parseTagValue: false,
    processEntities: false,
  }).parse(xml);
  const record = response.parse(
    envelope.Envelope?.Body?.GetStudentCertificatesResponse,
  );
  if (record.StudentID !== id || record.RequestReference !== reference)
    throw new Error("Unexpected response reference");
  const cards: RecordCard[] = [];
  function add(
    title: string,
    cert: z.infer<typeof certificate>,
    detail: [string, string],
  ) {
    cards.push({
      title,
      status: cert.CertificateStatus,
      tone: cert.CertificateStatus === "VALID" ? "ok" : "attention",
      fields: [
        detail,
        ["Certificate reference", cert.ProviderRecordReference],
        ["Issued", cert.IssueDate],
        ["Expires", cert.ExpiryDate],
      ],
    });
  }
  if (record.IncomeCertificate)
    add("Income certificate", record.IncomeCertificate, [
      "Annual income",
      new Intl.NumberFormat("en-IN", {
        style: "currency",
        currency: "INR",
      }).format(Number(record.IncomeCertificate.AnnualIncomeINR)),
    ]);
  if (record.CasteCertificate)
    add("Caste certificate", record.CasteCertificate, [
      "Category",
      record.CasteCertificate.Category,
    ]);
  if (!cards.length) throw new Error("Missing certificates");
  return cards;
}
