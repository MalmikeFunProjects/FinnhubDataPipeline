import Button from '@/components/Button';

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="bg-white rounded-lg shadow-lg p-6 max-w-md w-full">
        <h1 className="text-3xl font-bold text-blue-600 mb-4">
          Next.js + TypeScript + Tailwind
        </h1>
        <p className="text-gray-700 mb-6">
          This is a fully typed Next.js application with Tailwind CSS.
        </p>
        <div className="space-y-3">
          <Button variant="primary">Primary Button</Button>
          <Button variant="secondary" fullWidth>Secondary Button</Button>
          <Button variant="success" size="lg">Success Button</Button>
          <Button variant="danger" disabled>Danger Button</Button>
        </div>
      </div>
    </main>
  );
}

