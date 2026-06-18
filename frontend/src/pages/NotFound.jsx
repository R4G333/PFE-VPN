import { Link } from "react-router-dom";

export default function NotFound() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-canvas px-4">
      <div className="max-w-md text-center">
        <div className="mb-4 text-6xl font-bold text-ink-300">404</div>
        <h1 className="mb-2 text-lg font-semibold text-ink-900">Page not found</h1>
        <p className="mb-6 text-sm text-ink-500">
          The page you are looking for does not exist or has been moved.
        </p>
        <Link to="/" className="btn-primary inline-flex px-4 py-2">
          Go Home
        </Link>
      </div>
    </div>
  );
}
