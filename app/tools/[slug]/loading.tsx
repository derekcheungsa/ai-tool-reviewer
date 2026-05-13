export default function ToolLoading() {
  return (
    <div className="container mx-auto max-w-7xl px-4 py-8">
      <div className="animate-pulse space-y-8">
        {/* Breadcrumb */}
        <div className="h-4 w-32 bg-secondary rounded" />

        {/* Header */}
        <div className="space-y-3">
          <div className="flex gap-3">
            <div className="h-6 w-24 bg-secondary rounded" />
            <div className="h-6 w-40 bg-secondary rounded" />
          </div>
          <div className="h-9 w-64 bg-secondary rounded" />
          <div className="h-5 w-full max-w-2xl bg-secondary rounded" />
        </div>

        {/* Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-28 bg-card border border-border rounded-xl" />
          ))}
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 h-80 bg-card border border-border rounded-xl" />
          <div className="h-80 bg-card border border-border rounded-xl" />
        </div>

        {/* Reviews */}
        <div className="space-y-3">
          <div className="h-7 w-32 bg-secondary rounded" />
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-32 bg-card border border-border rounded-xl" />
          ))}
        </div>
      </div>
    </div>
  );
}
