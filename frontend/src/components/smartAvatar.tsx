import { cn } from "@/lib/utils"
import { Avatar, AvatarFallback, AvatarImage } from "./ui/avatar"
import { Skeleton } from "./ui/skeleton"

interface FallbackAvatarProps {
  profilePicture: string | null | undefined
  name: string | null | undefined
  loading?: boolean
  className?: string
}
export default function SmartAvatar({
  profilePicture,
  name,
  loading = false,
  className,
}: FallbackAvatarProps) {
  return (
    <Avatar className={cn("h-32 w-32 text-4xl", className)}>
      {!loading ? (
        <>
          {profilePicture && <AvatarImage src={profilePicture} />}
          <AvatarFallback>
            {(name || "")
              .split(" ")
              .map((n) => n[0])
              .join("")}
          </AvatarFallback>
        </>
      ) : (
        <Skeleton className="h-full w-full" />
      )}
    </Avatar>
  )
}
