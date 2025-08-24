import './globals.css'

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <head>
        <title>PDF to Excel SaaS - Coming Soon</title>
        <meta name="description" content="Transform PDFs to Excel - Coming Soon" />
      </head>
      <body>
        <div id="root">{children}</div>
      </body>
    </html>
  )
}