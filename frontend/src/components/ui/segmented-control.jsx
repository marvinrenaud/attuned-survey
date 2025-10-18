"use client"

import * as React from "react"
import { cn } from "@/lib/utils"

const SegmentedControl = React.forwardRef(({ 
  className, 
  options, 
  value, 
  onValueChange, 
  name,
  "data-testid": dataTestId,
  ...props 
}, ref) => {
  return (
    <div 
      className={cn("segmented-control", className)}
      role="radiogroup"
      data-testid={dataTestId}
      {...props}
    >
      <div className="segmented-options">
        {options.map((option) => (
          <React.Fragment key={option.value}>
            <input
              type="radio"
              id={`${name}-${option.value}`}
              name={name}
              value={option.value}
              checked={value === option.value}
              onChange={() => onValueChange(option.value)}
              className="segmented-input"
            />
            <label
              htmlFor={`${name}-${option.value}`}
              className="segmented-label"
            >
              {option.label}
            </label>
          </React.Fragment>
        ))}
      </div>
    </div>
  )
})

SegmentedControl.displayName = "SegmentedControl"

export { SegmentedControl }
