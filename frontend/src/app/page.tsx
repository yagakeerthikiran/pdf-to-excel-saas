import ProductionUploadCard from "@/components/ProductionUploadCard";
import Link from "next/link";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="text-center mb-8">
        <h1 className="text-4xl font-bold">PDF to Excel Converter</h1>
        <p className="mt-4 text-lg">
          The best tool to convert your PDF files into editable Excel spreadsheets.
        </p>
        <div className="mt-6">
          <Link 
            href="/dashboard" 
            className="text-indigo-600 hover:text-indigo-500 font-medium"
          >
            View Dashboard →
          </Link>
        </div>
      </div>
      
      <ProductionUploadCard />
      
      <div className="mt-8 text-center">
        <p className="text-sm text-gray-600">
          <span className="font-semibold">Free tier:</span> 5 conversions per day
        </p>
        <p className="text-sm text-gray-600 mt-1">
          <Link href="/pricing" className="text-indigo-600 hover:text-indigo-500">
            Upgrade to Pro for unlimited conversions
          </Link>
        </p>
      </div>
    </main>
  );
}