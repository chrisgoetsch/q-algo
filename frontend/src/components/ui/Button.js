import { jsx as _jsx } from "react/jsx-runtime";
import * as React from "react";
import { cn } from "@/lib/utils";
const Button = React.forwardRef(({ className, ...props }, ref) => {
    return (_jsx("button", { ref: ref, className: cn("inline-flex items-center justify-center rounded-xl bg-blue-600 px-4 py-2 text-white font-medium shadow hover:bg-blue-700 transition", className), ...props }));
});
Button.displayName = "Button";
export { Button };
