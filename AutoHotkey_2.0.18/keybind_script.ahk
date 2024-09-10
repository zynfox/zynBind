
        ctrld::
        {
            ; Use FormatTime to get the current date in MM/dd/yyyy format
            currentDate := FormatTime(A_Now, "MM/dd/yyyy")
            ; Add a space before or after the formatted date
            formattedDate := "" currentDate " "
            ; Send formatted input
            SendInput(formattedDate)
            return
        }
        