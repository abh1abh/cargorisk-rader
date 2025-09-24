"use client";

import { useEffect } from "react";
import Link from "next/link";

export default function GlobalError({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
    useEffect(() => {
        // Log to your APM / Sentry here if you like
        // e.g., Sentry.captureException(error)
        console.error("GlobalError:", error);
    }, [error]);

    return (
        <html>
            <body className="min-h-screen bg-gray-50 text-gray-900">
                <div className="mx-auto max-w-xl p-6">
                    <div className="rounded-2xl border bg-white p-6 shadow-sm">
                        <h1 className="text-2xl font-semibold">Something went wrong</h1>
                        <p className="mt-2 text-sm text-gray-600">
                            An unexpected error occurred while rendering this page.
                        </p>

                        {error?.message ? (
                            <pre className="mt-4 overflow-auto rounded-lg bg-gray-100 p-3 text-sm text-gray-800">
                                {error.message}
                            </pre>
                        ) : null}

                        {error?.digest ? (
                            <p className="mt-2 text-xs text-gray-500">
                                Error code: <code>{error.digest}</code>
                            </p>
                        ) : null}

                        <div className="mt-6 flex gap-3">
                            <button
                                onClick={() => reset()}
                                className="rounded-xl border px-4 py-2 text-sm font-medium hover:bg-gray-50">
                                Try again
                            </button>
                            <Link
                                href="/"
                                className="rounded-xl border px-4 py-2 text-sm font-medium hover:bg-gray-50">
                                Go home
                            </Link>
                        </div>
                    </div>

                    <p className="mt-4 text-xs text-gray-500">
                        If this keeps happening, contact support and include the error code.
                    </p>
                </div>
            </body>
        </html>
    );
}
