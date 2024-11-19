; Example code that displays an RGB gradient onto the display

MOV r0 0      ; x coordinate
MOV r1 0      ; y coordinate
MOV r2 0      ; temporary calculation storage
MOV r3 200    ; height (200 pixels)
MOV r4 200    ; width (200 pixels)
MOV r6 0      ; ram pointer

MOV [r6] 0    ; initialize counter

; Start outer loop (y coordinate)
YLOOP:
    ; Start inner loop (x coordinate)
    MOV r0 0
    XLOOP:
        CALL COUNTER

        ; Calculate color components based on position
        ; Red: peaks in top-right (x + y)
        MOV r7 r0          ; Load x coordinate
        ADD r7 r1          ; Add y coordinate
        MUL r7 255        ; Multiply by 255
        DIV r7 400        ; Normalize (max possible value is 400)
        SHL r7 16         ; Shift to red position

        ; Green: peaks in bottom-left (inverse of x + inverse of y)
        MOV r5 r4         ; Load max width
        SUB r5 r0         ; Subtract x (inverse x)
        ADD r5 r1         ; Add y
        MUL r5 255        ; Multiply by 255
        DIV r5 400        ; Normalize
        SHL r5 8          ; Shift to green position

        ; Blue: peaks in top-left (inverse of x + y)
        MOV r2 r4        ; Load max width
        SUB r2 r0         ; Subtract x (inverse x)
        ADD r2 r3        ; Load max height
        SUB r2 r1         ; Subtract y (inverse y)
        MUL r2 255        ; Multiply by 255
        DIV r2 400        ; Normalize

        ; Combine all colors
        ADD r7 r5         ; Add green component
        ADD r7 r2         ; Add blue component
        
        ; Set color and draw pixel
        COL r7
        DSP r0 r1
        
        ; Increment x and check if we reached width
        INC r0
        CMP r0 r4
        JN XLOOP
    
    ; Increment y and check if we reached height
    INC r1
    CMP r1 r3
    JN YLOOP

HLT

; Increment counter and return
COUNTER: ; This is just an exmple, its not needed for the gradient calculation
    INC [r6] ; increment counter
    PRT [r6] ; print counter value
    RET
