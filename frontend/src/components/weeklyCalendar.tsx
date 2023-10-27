import { cn } from "@/lib/utils"
import React, { useEffect, useRef, useState } from "react"
import {
  setDay,
  setWeek,
  format,
  getWeek,
  isSameDay,
  areIntervalsOverlapping,
  startOfDay,
  endOfDay,
  differenceInMinutes,
  startOfWeek,
  setMinutes,
  roundToNearestMinutes,
  min,
} from "date-fns"
import { Button } from "./ui/button"
import { ChevronLeft, ChevronRight } from "lucide-react"

interface InteractiveInterval {
  interval: Interval
  title?: string
  componentProps: React.ComponentProps<"div">
}

interface WeeklyCalendarProps {
  className?: string
  interactiveIntervals: InteractiveInterval[]
  onCalendarClick?: (dateClicked: Date) => void
}
export default function WeeklyCalendar({
  className,
  interactiveIntervals,
  onCalendarClick = () => {},
}: WeeklyCalendarProps) {
  // Below required for scrolling the axis labels
  const [calHeight, setCalHeight] = useState(0)
  const [calWidth, setCalWidth] = useState(0)
  const scrollRef = useRef<HTMLDivElement>(null)
  const topRef = useRef<HTMLDivElement>(null)
  const sideRef = useRef<HTMLDivElement>(null)

  // Week offset refers to the number of weeks from the current week that the user is viewing
  const [weekOffset, setViewWeek] = useState(getWeek(new Date()))
  // Week date is the start Date obj of the week the user is viewing
  const [weekDate, setWeekDate] = useState(new Date())

  useEffect(() => {
    setWeekDate(startOfWeek(setWeek(new Date(), weekOffset)))
  }, [weekOffset])

  useEffect(() => {
    // This useEffect runs on component mount
    // It sets up window.resize event so that other variables/effects can rely on
    // the calendar width.
    // It also scrolls down to 7am by default
    const onResize = () => {
      setCalWidth(scrollRef.current?.scrollWidth || 0)
    }

    window.onresize = onResize
    if (scrollRef.current) {
      const height = scrollRef.current.scrollHeight
      setCalHeight(height)
      setCalWidth(scrollRef.current.scrollWidth)
      // scroll down to 7am for better UX
      scrollRef.current.scrollTo(0, (height / 24) * 7 + 10)
    }
    return () => window.removeEventListener("resize", onResize)
  }, [])

  const handleCalendarClick = (e: React.MouseEvent<HTMLDivElement>) => {
    const divElement = e.currentTarget
    const rect = divElement.getBoundingClientRect()
    const x = e.clientX - rect.left + divElement.scrollLeft
    const y = e.clientY - rect.top + divElement.scrollTop
    const day = (x / divElement.scrollWidth) * 7
    const hourOfDay = (y / divElement.scrollHeight) * 24
    const clickedDate = roundToNearestMinutes(
      setMinutes(setDay(weekDate, day), hourOfDay * 60),
      { nearestTo: 15 },
    )
    onCalendarClick(clickedDate)
  }

  return (
    <div className="flex h-full w-full flex-col gap-3 overflow-hidden">
      <div className="ml-[50px] flex items-center gap-2">
        {/* Calendar Controls */}
        <Button variant="outline" onClick={() => setViewWeek(weekOffset - 1)}>
          <ChevronLeft />
        </Button>
        <Button variant="outline" onClick={() => setViewWeek(weekOffset + 1)}>
          <ChevronRight />
        </Button>
        <h2 className="px-4 text-3xl text-foreground">
          {format(weekDate, "MMMM yyyy")}
        </h2>
      </div>

      <div className="grid h-full w-full grid-cols-[75px_1fr] grid-rows-[75px_1fr] overflow-hidden">
        {/* Calendar x-axis labels (i.e. day of the week) */}
        <div ref={topRef} className="col-start-2 col-end-3 overflow-x-hidden">
          <div
            style={{
              width: calWidth,
            }}
            className="grid h-full grid-cols-7 place-items-center items-end pb-2 text-muted-foreground"
          >
            {Array.from(Array(7).keys()).map((dayIndex) => {
              const currDate = setDay(weekDate, dayIndex)
              const isToday = isSameDay(new Date(), currDate)
              return (
                <div
                  key={dayIndex}
                  className={cn(
                    "whitespace-nowrap rounded-md px-5 py-2 text-center",
                    {
                      "bg-primary": isToday,
                      "text-primary-foreground": isToday,
                    },
                  )}
                >
                  <span>{format(currDate, "iii do")}</span>
                </div>
              )
            })}
          </div>
        </div>

        <div ref={sideRef} className="row-span-2 mr-2 overflow-y-hidden">
          {/* Calendar y-axis labels (i.e. hours of the day) */}
          <div
            style={{
              height: calHeight,
            }}
            className="grid grid-rows-[repeat(24,1fr)]"
          >
            {Array.from(Array(24).keys()).map((hour) => (
              <div
                className="-translate-y-[0.75em] text-right text-sm text-muted-foreground"
                key={hour}
              >
                {hour !== 0 && format(new Date().setHours(hour), "h aaa")}
              </div>
            ))}
          </div>
        </div>

        {/* Actual Calendar */}
        <div
          onClick={handleCalendarClick}
          onScroll={(e) => {
            // Scrolling the x and y axis (necessary since we want them to be sticky as well)
            sideRef.current?.scrollTo(0, e.currentTarget.scrollTop)
            topRef.current?.scrollTo(e.currentTarget.scrollLeft, 0)
          }}
          ref={scrollRef}
          className={cn(
            "grid h-full w-full grid-cols-[repeat(7,minmax(100px,1fr))] overflow-auto ",
            className,
          )}
        >
          {/* Creating columns for each day */}
          {Array.from(Array(7).keys()).map((dayIndex) => {
            return (
              <DayCol
                date={setDay(weekDate, dayIndex)}
                key={dayIndex}
                interactiveIntervals={interactiveIntervals}
              />
            )
          })}
        </div>
      </div>
    </div>
  )
}

const MINUTES_IN_DAY = 60 * 24
interface DayColProps {
  style?: React.CSSProperties
  className?: string
  date: Date
  interactiveIntervals: InteractiveInterval[]
}
function DayCol({ className, style, interactiveIntervals, date }: DayColProps) {
  const dayInterval = {
    start: startOfDay(date),
    end: endOfDay(date),
  }
  const colRef = useRef<HTMLDivElement>(null)
  const [colHeight, setColHeight] = useState(0)

  useEffect(() => {
    // This useEffect runs on component mount
    // sets initial column height and resize hook for other variabnles/effects to use
    setColHeight(colRef.current?.scrollHeight || 0)
    const onResize = () => {
      setColHeight(colRef.current?.scrollHeight || 0)
    }
    window.onresize = onResize
    return () => window.removeEventListener("resize", onResize)
  }, [])

  // remove any intervals that dont occur within this day
  interactiveIntervals = interactiveIntervals.filter((interval) =>
    areIntervalsOverlapping(dayInterval, interval.interval),
  )

  // little bit of math to calculate x offset and height of absolute positioned interval elements
  const intervalElements = interactiveIntervals.map(
    ({ interval, title, componentProps: { className, ...componentProps } }) => {
      const startY =
        (differenceInMinutes(interval.start, startOfDay(date)) /
          MINUTES_IN_DAY) *
        colHeight
      const height =
        (differenceInMinutes(
          min([interval.end, endOfDay(dayInterval.end)]),
          interval.start,
        ) /
          MINUTES_IN_DAY) *
        colHeight

      return (
        <div
          key={interval.start.toString()}
          className={cn(
            "absolute flex w-full flex-col bg-gray-400 p-2 text-xs ",
            className,
          )}
          style={{
            height,
            transform: `translateY(${startY}px)`,
          }}
          {...componentProps}
        >
          {title && <h4 className="font-bold">{title}</h4>}
          {`${format(interval.start, "h:mmaaa")} – ${format(
            interval.end,
            "h:mmaaa",
          )}`}
        </div>
      )
    },
  )
  return (
    <div
      ref={colRef}
      style={style}
      className={cn(
        "relative grid grid-rows-[repeat(24,1fr)] border border-black/50",
        className,
      )}
    >
      {intervalElements}
      {Array.from(Array(24).keys()).map((hourIndex) => {
        return (
          <div
            key={hourIndex}
            className={cn("min-h-[75px] border border-black/10")}
          />
        )
      })}
      <div className="absolute -z-20 h-full w-full bg-red-100" />
    </div>
  )
}
