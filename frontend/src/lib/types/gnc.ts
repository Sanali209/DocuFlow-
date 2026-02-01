export interface GNCCommand {
    type: string; // G00, G01, G02, G03
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
    corner_count: number;
    length: number;
}

export interface GNCPart {
    id: number;
    contours: GNCContour[];
    name?: string;
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
