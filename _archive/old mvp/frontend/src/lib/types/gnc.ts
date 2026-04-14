export interface GNCCommand {
    type: string; // G00, G01, M30, etc.
    command?: string; // G, M, T
    value?: number; // 0, 1, 30
    x?: number;
    y?: number;
    i?: number;
    j?: number;
    line_number?: number;
    original_text?: string;
}

export interface GNCContour {
    id: number;
    commands: GNCCommand[];
    is_closed: boolean;
    is_hole: boolean;
    metadata: Record<string, any>;
    corner_count: number;
    length: number;
}

export interface GNCPart {
    id: number;
    contours: GNCContour[];
    name?: string;
    metadata: Record<string, any>;
    corner_count: number;
}

export interface GNCSheet {
    parts: GNCPart[];
    metadata: Record<string, any>;
    total_parts: number;
    total_contours: number;
    material?: string;
    thickness?: number;
    width?: number;
    height?: number;
}
