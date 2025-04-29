import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import * as React from "react";
import * as SliderPrimitive from "@radix-ui/react-slider";
import { cn } from "@/lib/utils";
const Slider = React.forwardRef(({ className, ...props }, ref) => (_jsxs(SliderPrimitive.Root, { ref: ref, className: cn("relative flex w-full touch-none select-none items-center", className), ...props, children: [_jsx(SliderPrimitive.Track, { className: "relative h-2 w-full grow overflow-hidden rounded-full bg-zinc-700", children: _jsx(SliderPrimitive.Range, { className: "absolute h-full bg-blue-500" }) }), _jsx(SliderPrimitive.Thumb, { className: "block h-5 w-5 rounded-full border-2 border-blue-500 bg-white shadow-sm transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2" })] })));
Slider.displayName = "Slider";
export { Slider };
