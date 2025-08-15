import SimpleUploadCard from "@/components/SimpleUploadCard";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="text-center mb-8">
        <h1 className="text-4xl font-bold">PDF to Excel Converter</h1>
        <p className="mt-4 text-lg">
          The best tool to convert your PDF files into editable Excel spreadsheets.
        </p>
      </div>
      
      <SimpleUploadCard />
    </main>
  );
}