import FileUpload from '@/components/FileUpload'

export default function DashboardPage() {
  return (
    <div className="flex min-h-screen flex-col items-center p-24">
      <div className="w-full max-w-lg text-center">
        <h1 className="text-4xl font-bold">Dashboard</h1>
        <p className="mt-4 text-lg">
          Welcome to your dashboard. Upload your PDF file below to get started.
        </p>
        <div className="mt-8">
          <FileUpload />
        </div>
      </div>
    </div>
  )
}
