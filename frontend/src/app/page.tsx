export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-24">
      <div className="z-10 max-w-5xl w-full items-center justify-between font-mono text-sm lg:flex">
        <h1 className="text-4xl font-bold text-center">
          Welcome to Admire HRMS
        </h1>
      </div>
      
      <div className="mb-32 grid text-center lg:max-w-5xl lg:w-full lg:mb-0 lg:grid-cols-4 lg:text-left">
        <div className="group rounded-lg border border-transparent px-5 py-4 transition-colors hover:border-gray-300 hover:bg-gray-100">
          <h2 className="mb-3 text-2xl font-semibold">
            Employee Management
          </h2>
          <p className="m-0 max-w-[30ch] text-sm opacity-50">
            Manage employee information, departments, and organizational structure.
          </p>
        </div>

        <div className="group rounded-lg border border-transparent px-5 py-4 transition-colors hover:border-gray-300 hover:bg-gray-100">
          <h2 className="mb-3 text-2xl font-semibold">
            Attendance Tracking
          </h2>
          <p className="m-0 max-w-[30ch] text-sm opacity-50">
            Biometric attendance system with face recognition technology.
          </p>
        </div>

        <div className="group rounded-lg border border-transparent px-5 py-4 transition-colors hover:border-gray-300 hover:bg-gray-100">
          <h2 className="mb-3 text-2xl font-semibold">
            Leave Management
          </h2>
          <p className="m-0 max-w-[30ch] text-sm opacity-50">
            Handle leave requests, approvals, and balance tracking.
          </p>
        </div>

        <div className="group rounded-lg border border-transparent px-5 py-4 transition-colors hover:border-gray-300 hover:bg-gray-100">
          <h2 className="mb-3 text-2xl font-semibold">
            Payroll System
          </h2>
          <p className="m-0 max-w-[30ch] text-sm opacity-50">
            Automated payroll processing and salary management.
          </p>
        </div>
      </div>
    </main>
  )
}