export class ProviderError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

export function setting(name: string): string {
  const value = process.env[name];
  if (!value)
    throw new ProviderError(
      503,
      "Portal connection settings are incomplete. Contact the demo operator.",
    );
  return value;
}

export async function call(path: string, init: RequestInit): Promise<Response> {
  const base = setting("BACKEND_URL");
  let response: Response;
  try {
    response = await fetch(new URL(path, base), {
      ...init,
      cache: "no-store",
      redirect: "error",
      signal: AbortSignal.timeout(8000),
    });
  } catch {
    throw new ProviderError(
      503,
      "The department service is unavailable. Please retry the lookup.",
    );
  }
  if (response.status === 401 || response.status === 403) {
    throw new ProviderError(
      502,
      "Department authentication failed. Contact the demo operator.",
    );
  }
  if (response.status === 404)
    throw new ProviderError(
      404,
      "The department has no matching evidence for this student ID.",
    );
  if (!response.ok)
    throw new ProviderError(
      503,
      "The department could not complete the lookup. Please try again.",
    );
  return response;
}
