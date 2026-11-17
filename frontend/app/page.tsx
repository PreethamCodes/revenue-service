import Register from "./register";
export const dynamic = "force-dynamic";
export default function Page() {
  return (
    <>
      <header>
        <div className="frame mast flex items-center justify-between">
          <div className="brand">
            <span className="seal" aria-hidden="true">
              RD
            </span>
            <div>
              <strong>Revenue Department</strong>
              <small>MahaSetu · Department portal</small>
            </div>
          </div>
          <span className="demo">Synthetic demo</span>
        </div>
      </header>
      <main className="frame">
        <div className="intro">
          <span className="overline">Land & revenue</span>
          <h1>Certificate register</h1>
          <p>
            Review income and caste certificates held by the Revenue Department.
          </p>
        </div>
        {process.env.PORTAL_DEMO_ACCESS === "enabled" ? (
          <Register />
        ) : (
          <section className="panel">
            <h2>Demo access is closed</h2>
            <p>Contact the demo operator to open this register.</p>
          </section>
        )}
      </main>
      <footer className="frame">
        MahaSetu <span> / </span> Revenue Department simulator
      </footer>
    </>
  );
}
