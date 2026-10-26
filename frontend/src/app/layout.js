import "./globals.css";
import { AuthProvider } from "@/context/AuthContext";

export const metadata = {
  title: "AI SaaS Workspace | Grounded RAG & Document Intelligence",
  description: "Enterprise multi-tenant document intelligence with verifiable citations, zero-leak isolation, and transparent token quotas.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body suppressHydrationWarning>
        <AuthProvider>
          {children}
        </AuthProvider>
      </body>
    </html>
  );
}
