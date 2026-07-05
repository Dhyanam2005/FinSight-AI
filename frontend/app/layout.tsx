import "./globals.css";

export const metadata = {
  title: "FinSight AI",
  description: "AI-powered financial research assistant",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body suppressHydrationWarning>{children}</body>
    </html>
  );
}