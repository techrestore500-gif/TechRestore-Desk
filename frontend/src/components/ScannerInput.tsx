import { KeyboardEvent } from "react";

export function ScannerInput({
    value,
    onChange,
    onScanSubmit,
    placeholder,
}: {
    value: string;
    onChange: (value: string) => void;
    onScanSubmit: (value: string) => void;
    placeholder: string;
}) {
    const onKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
        if (event.key === "Enter") {
            event.preventDefault();
            onScanSubmit(value.trim());
        }
    };

    return (
        <input
            value={value}
            onChange={(event) => onChange(event.target.value)}
            onKeyDown={onKeyDown}
            placeholder={placeholder}
            autoCapitalize="off"
            autoCorrect="off"
            spellCheck={false}
            style={{
                width: "100%",
                padding: "10px 12px",
                borderRadius: "10px",
                border: "1px solid #bfd0cb",
                backgroundColor: "#fff",
            }}
        />
    );
}
