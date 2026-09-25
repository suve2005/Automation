import subprocess
import os
from fastmcp import FastMCP

# Initialize the server
mcp = FastMCP("KiCad_MCP_Server")

@mcp.tool
def ping() -> str:
    """A dummy tool to test the MCP connection. Returns 'pong'."""
    return "pong"

@mcp.tool
def run_erc(schematic_filename: str) -> str:
    """Runs KiCad ERC on a schematic file."""
    target_dir = "/app/project"
    sch_path = os.path.join(target_dir, schematic_filename)
    report_path = os.path.join(target_dir, "erc_report.rpt")
    error_log = os.path.join(target_dir, "Errors.txt")

    if not os.path.exists(sch_path):
        return f"Error: Could not find '{schematic_filename}'."

    # Force KiCad into headless rendering mode
    env = dict(os.environ, QT_QPA_PLATFORM="offscreen")

    result = subprocess.run(
        ["kicad-cli", "sch", "erc", "--output", report_path, sch_path],
        capture_output=True,
        text=True,
        cwd=target_dir,
        env=env
    )

    if result.returncode != 0:
        if os.path.exists(report_path):
            with open(report_path, "r") as f:
                report_content = f.read()
        else:
            # If the file wasn't created, capture the raw system crash log
            report_content = f"KICAD CLI CRASHED:\nExit Code: {result.returncode}\nSTDERR: {result.stderr}\nSTDOUT: {result.stdout}"
        
        with open(error_log, "a") as f:
            f.write(f"\n--- ERC VIOLATIONS: {schematic_filename} ---\n{report_content}\n")
            
        return "ERC Failed. Check Errors.txt for details."

    return f"ERC passed successfully for {schematic_filename}."


@mcp.tool
def run_drc(pcb_filename: str) -> str:
    """Runs KiCad DRC on a PCB file."""
    target_dir = "/app/project"
    pcb_path = os.path.join(target_dir, pcb_filename)
    report_path = os.path.join(target_dir, "drc_report.rpt")
    error_log = os.path.join(target_dir, "Errors.txt")

    if not os.path.exists(pcb_path):
        return f"Error: Could not find '{pcb_filename}'."

    env = dict(os.environ, QT_QPA_PLATFORM="offscreen")

    result = subprocess.run(
        ["kicad-cli", "pcb", "drc", "--output", report_path, pcb_path],
        capture_output=True,
        text=True,
        cwd=target_dir,
        env=env
    )

    if result.returncode != 0:
        if os.path.exists(report_path):
            with open(report_path, "r") as f:
                report_content = f.read()
        else:
            report_content = f"KICAD CLI CRASHED:\nExit Code: {result.returncode}\nSTDERR: {result.stderr}\nSTDOUT: {result.stdout}"
        
        with open(error_log, "a") as f:
            f.write(f"\n--- DRC VIOLATIONS: {pcb_filename} ---\n{report_content}\n")
            
        return "DRC Failed. Check Errors.txt for details."

    return f"DRC passed successfully for {pcb_filename}."


@mcp.tool
def read_errors() -> str:
    """Reads the Errors.txt file."""
    error_log = "/app/project/Errors.txt"
    if not os.path.exists(error_log):
        return "Errors.txt not found."
    with open(error_log, "r") as f:
        content = f.read()
    return content if content.strip() else "Errors.txt is empty."

@mcp.tool
def generate_bom(schematic_filename: str) -> str:
    """Exports a BOM (Bill of Materials) in CSV format from the schematic."""
    target_dir = "/app/project"
    sch_path = os.path.join(target_dir, schematic_filename)
    output_name = schematic_filename.replace(".kicad_sch", "_BOM.csv")
    bom_path = os.path.join(target_dir, output_name)

    if not os.path.exists(sch_path):
        return f"Error: Could not find '{schematic_filename}'."

    env = dict(os.environ, QT_QPA_PLATFORM="offscreen")
    
    result = subprocess.run(
        ["kicad-cli", "sch", "export", "bom", "--output", bom_path, sch_path],
        capture_output=True,
        text=True,
        cwd=target_dir,
        env=env
    )

    if result.returncode != 0:
        return f"BOM Generation Failed:\n{result.stderr}"
        
    return f"BOM successfully generated at {output_name}"


@mcp.tool
def generate_gerbers(pcb_filename: str) -> str:
    """Exports manufacturing Gerber and Drill files into a dedicated folder."""
    target_dir = "/app/project"
    pcb_path = os.path.join(target_dir, pcb_filename)
    gerber_dir = os.path.join(target_dir, "Gerbers")

    if not os.path.exists(pcb_path):
        return f"Error: Could not find '{pcb_filename}'."

    os.makedirs(gerber_dir, exist_ok=True)
    env = dict(os.environ, QT_QPA_PLATFORM="offscreen")
    

    gerber_result = subprocess.run(
        ["kicad-cli", "pcb", "export", "gerbers", "--output", gerber_dir, pcb_path],
        capture_output=True,
        text=True,
        cwd=target_dir,
        env=env
    )

    if gerber_result.returncode != 0:
        return f"Gerber Generation Failed:\n{gerber_result.stderr}"
        

    drill_result = subprocess.run(
        ["kicad-cli", "pcb", "export", "drill", "--output", gerber_dir, pcb_path],
        capture_output=True,
        text=True,
        cwd=target_dir,
        env=env
    )

    if drill_result.returncode != 0:
        return f"Drill File Generation Failed:\n{drill_result.stderr}"

    return "Gerbers and Drill files successfully generated in the 'Gerbers' folder."


@mcp.tool
def auto_route(pcb_filename: str) -> str:
    """
    Executes the Java-based Freerouting engine headlessly.
    Converts the PCB to a DSN, routes it, and outputs an SES file.
    """
    # Import KiCad's native Python API directly
    import pcbnew 
    
    target_dir = "/app/project"
    pcb_path = os.path.join(target_dir, pcb_filename)
    dsn_path = os.path.join(target_dir, pcb_filename.replace(".kicad_pcb", ".dsn"))
    ses_path = os.path.join(target_dir, pcb_filename.replace(".kicad_pcb", ".ses"))

    if not os.path.exists(pcb_path):
        return f"Error: Could not find '{pcb_filename}'."

    # Step 1: Export DSN using the Python API (Bypassing kicad-cli entirely)
    try:
        board = pcbnew.LoadBoard(pcb_path)
        pcbnew.ExportSpecctraDSN(board, dsn_path)
    except Exception as e:
        return f"DSN Export Failed via Python API:\n{str(e)}"

    if not os.path.exists(dsn_path):
        return "DSN Export failed silently. No file was generated."

# Step 2: Execute the Freerouting JAR via Xvfb (Virtual Framebuffer)
    env = dict(os.environ, QT_QPA_PLATFORM="offscreen")
    route_result = subprocess.run(
        ["xvfb-run", "--auto-servernum", "java", "-jar", "/app/freerouting.jar", "-de", dsn_path, "-do", ses_path, "-mp", "10"],
        capture_output=True,
        text=True,
        cwd=target_dir,
        env=env
    )
    
    # We now capture both stderr and stdout to prevent silent failures
    if route_result.returncode != 0:
        return f"Freerouting Engine Failed:\nSTDERR: {route_result.stderr}\nSTDOUT: {route_result.stdout}"

    return f"Auto-routing complete! The routed traces are saved as {os.path.basename(ses_path)}."

if __name__ == "__main__":
    mcp.run()