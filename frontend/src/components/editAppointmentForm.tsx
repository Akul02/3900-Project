import { Control, Controller, useForm } from "react-hook-form"
import { PopoverContent, Popover, PopoverTrigger } from "./ui/popover"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Calendar } from "./ui/calendar"
import { Button } from "./ui/button"
import { cn } from "@/lib/utils"
import { ArrowRight, CalendarIcon } from "lucide-react"
import {
  addMinutes,
  format,
  parse,
  setMinutes,
  startOfDay,
  startOfWeek,
} from "date-fns"
import { flatten, range } from "lodash"
import { z } from "zod"
import { zodResolver } from "@hookform/resolvers/zod"
import LoadingButton from "./loadingButton"
import { useState } from "react"

const zodSchema = z
  .object({
    globalErrors: z.string().optional(), // ts bandaid fix for global errors with zod resolver/refine
    date: z.date(),
    startTime: z.string().regex(/^[0-9]{2}:[0-9]{2} [A|P]M$/),
    endTime: z.string().regex(/^[0-9]{2}:[0-9]{2} [A|P]M$/),
  })
  .refine(
    ({ startTime, endTime }) => {
      if (startTime && endTime) {
        return (
          processTimeInputToDate(new Date(), startTime) <
          processTimeInputToDate(new Date(), endTime)
        )
      }
      return true
    },
    {
      message: "Start time should be before end time",
      path: ["globalErrors"],
    },
  )

const processTimeInputToDate = (date: Date, time: string) => {
  return parse(time, "hh:mm aa", date)
}

interface EditAppointmentFormProps {
  cancelFn: () => void
  submitFn: (start: Date, end: Date) => Promise<boolean>
  startTime?: Date
  endTime?: Date
}
export default function EditAppointmentForm({
  cancelFn,
  submitFn,
  startTime,
  endTime = startTime && addMinutes(startTime, 60),
}: EditAppointmentFormProps) {
  const {
    control,
    handleSubmit,
    getValues,
    setError,
    setValue,
    formState: { errors },
  } = useForm<z.infer<typeof zodSchema>>({
    resolver: zodResolver(zodSchema),
    mode: "onChange",
    reValidateMode: "onChange",
    defaultValues: {
      date: startTime && startOfDay(startTime),
      startTime: startTime && format(startTime, "hh:mm aa"),
      endTime: endTime && format(endTime, "hh:mm aa"),
    },
  })
  const [isSubmitting, setIsSubmitting] = useState(false)
  const onSubmit = async ({
    date,
    startTime,
    endTime,
  }: z.infer<typeof zodSchema>) => {
    setIsSubmitting(true)
    await submitFn(
      processTimeInputToDate(date, startTime),
      processTimeInputToDate(date, endTime),
    )
    setIsSubmitting(false)
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-2">
      <div className="flex items-start gap-2">
        <div className="flex flex-col">
          <Controller
            control={control}
            name="date"
            render={({ field }) => (
              <Popover>
                <PopoverTrigger asChild>
                  <Button variant={"outline"} className={cn()}>
                    <CalendarIcon className="mr-2 h-4 w-4" />
                    {field.value ? (
                      format(field.value, "PPP")
                    ) : (
                      <span>Pick a date</span>
                    )}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0">
                  <Calendar
                    mode="single"
                    selected={field.value}
                    onSelect={(date) => field.onChange(date)}
                    initialFocus
                  />
                </PopoverContent>
              </Popover>
            )}
          />
          {errors.date && (
            <div className="text-destructive">* {errors.date.message}</div>
          )}
        </div>
        <div className="flex flex-col">
          <TimeControlledInput
            control={control}
            name="startTime"
            placeholder="Start Time"
          />
          {errors.startTime && (
            <div className="text-destructive">* {errors.startTime.message}</div>
          )}
        </div>
        <ArrowRight className="mt-2" />
        <div className="flex flex-col">
          <TimeControlledInput
            control={control}
            name="endTime"
            placeholder="End Time"
          />
          {errors.endTime && (
            <div className="text-destructive">* {errors.endTime.message}</div>
          )}
        </div>
      </div>
      {errors.globalErrors && (
        <div className="text-destructive">* {errors.globalErrors.message}</div>
      )}
      <div className="flex justify-end gap-2">
        <Button onClick={cancelFn} type="button" variant={"ghost"}>
          Cancel
        </Button>
        <LoadingButton isLoading={isSubmitting} type="submit">
          Submit
        </LoadingButton>
      </div>
    </form>
  )
}

interface TimeControlledInputProps {
  control: Control<z.infer<typeof zodSchema>>
  name: "startTime" | "endTime"
  placeholder: string
}
function TimeControlledInput({
  control,
  name,
  placeholder,
}: TimeControlledInputProps) {
  return (
    <Controller
      control={control}
      name={name}
      render={({ field }) => (
        <Select onValueChange={field.onChange} defaultValue={field.value}>
          <SelectTrigger className="w-fit">
            <SelectValue placeholder={placeholder} />
          </SelectTrigger>
          <SelectContent className="max-h-[300px]">
            {flatten(
              range(24).map((hour) =>
                range(0, 60, 15).map((minute) => {
                  let date = startOfWeek(new Date())
                  date = setMinutes(date, hour * 60 + minute)
                  const formattedTime = format(date, "hh:mm aa")
                  return (
                    <SelectItem value={formattedTime} key={formattedTime}>
                      {formattedTime}
                    </SelectItem>
                  )
                }),
              ),
            )}
          </SelectContent>
        </Select>
      )}
    />
  )
}
