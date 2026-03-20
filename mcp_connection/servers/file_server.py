from mcp.server.fastmcp import FastMCP
from pathlib import Path
import traceback

'''Tools for file access'''
# the agent is only allowed to access files in this root
SANDBOX_ROOT = Path(__file__).resolve().parent.parent
# directories for the agent to ignore
IGNORE_DIRS = {}
# files for the agent to ignore
IGNORE_FILES = {}

file_mcp_server = FastMCP()

@file_mcp_server.tool(
        name="read_file",
        description="read a file and return its content"
)
async def read_file(filename):

    file_path = (SANDBOX_ROOT / Path(filename)).resolve()

    try:
        with open(file=file_path, mode="r") as file:
            return file.read()
        
    except Exception as e:
        return f"Error reading file: {str(e)}"
    
@file_mcp_server.tool(
        name="list_files",
        description="list file for the given depth in the SANDBOX root"
)
def list_files(
    dir = "",
    max_depth: int = 3
):
    
    try:
        max_depth = int(max_depth)
    except TypeError:
        return "Max depth has to be of type 'int'"
    # c:users/.../copilot/.
    rel_path = (SANDBOX_ROOT / dir).resolve()
    
    tree = ""

    if not rel_path.exists():
        return "Path does not exists"
    if not str(rel_path).startswith(str(SANDBOX_ROOT)):
        return "Access denied"
    
    def build_file_tree(file_path: Path, max_depth=max_depth, indent=""):
        '''c:users/.../copilot , 3, ""
           c:users/.../copilot/agent , 2, ""'''
        nonlocal tree

        if max_depth < 0:
            return 
        
        try:
            for item in sorted(file_path.iterdir(), key=lambda p: (not p.is_dir(), p.name)):

                if item.name in IGNORE_DIRS or item.name in IGNORE_FILES:
                    continue
            
                '''
                agent/ (3)
                    agent/agent.py (2)
                    agent/execution_agent/
                        agent/execution_agent/execution_agent.py (1)
                        agent/execution_agent/utils
                            agent/execution_agent/utils/utils.py (0)
                mcp/
                    mcp/mcp_client.py
                    mcp/mcp_server.py
                other_folders...
                '''
                prefix = str(item.resolve()).removeprefix(str(SANDBOX_ROOT))
                tree += f"{indent}{prefix}\n"

                if item.is_dir():

                    file_path = item.resolve()
                    build_file_tree(file_path, max_depth - 1, indent + "    ")
        except Exception as e:
            traceback.print_exc
            return f"Exception has occured: {str(e)}"

    build_file_tree(rel_path)
    return tree

def main():
    # Initialize and run the server
    file_mcp_server.run(transport="stdio")

if __name__ == "__main__":
    main()