import { lookup } from "./provider";
import { ProviderError } from "./transport";
export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  const headers = { "Cache-Control": "no-store" };
  if (process.env.PORTAL_DEMO_ACCESS !== "enabled") {
    return Response.json(
      { message: "Demo access is closed." },
      { status: 403, headers },
    );
  }
  const id = new URL(request.url).searchParams.get("id") ?? "";
  if (!/^MHSTU[0-9]{4}$/.test(id)) {
    return Response.json(
      { message: "Enter a valid student ID." },
      { status: 400, headers },
    );
  }
  try {
    return Response.json({ cards: await lookup(id) }, { headers });
  } catch (error) {
    const status = error instanceof ProviderError ? error.status : 502;
    const message =
      error instanceof ProviderError
        ? error.message
        : "The department returned an unreadable response. Try again or contact the demo operator.";
    return Response.json({ message }, { status, headers });
  }
}
