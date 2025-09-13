import pandas as pd
import openai
import json
import time
from typing import Dict, List, Tuple, Optional
import os
import argparse
from difflib import SequenceMatcher

# Try to load dotenv for .env file support
try:
    from dotenv import load_dotenv
    load_dotenv()  # Load environment variables from .env file
except ImportError:
    print("Note: Install python-dotenv to use .env files: pip install python-dotenv")
    pass

class FootballRosterOrganizer:
    def __init__(self, openai_api_key: str):
        """
        Initialize the roster organizer with OpenAI API key.
        
        Args:
            openai_api_key: Your OpenAI API key
        """
        self.client = openai.OpenAI(api_key=openai_api_key)
        
    def load_excel_files(self, dress_list_path: str, player_info_path: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Load the Excel files for dress list and player info.
        
        Args:
            dress_list_path: Path to dress list Excel file
            player_info_path: Path to player info Excel file
            
        Returns:
            Tuple of (dress_list_df, player_info_df)
        """
        try:
            print(f"Loading dress list from: {dress_list_path}")
            print(f"Loading player info from: {player_info_path}")
            dress_list_df = pd.read_excel(dress_list_path)
            player_info_df = pd.read_excel(player_info_path)
            print(f"Dress list shape: {dress_list_df.shape}")
            print(f"Player info shape: {player_info_df.shape}")
            return dress_list_df, player_info_df
        except FileNotFoundError as e:
            raise Exception(f"File not found: {str(e)}")
        except Exception as e:
            raise Exception(f"Error loading Excel files: {str(e)}")
    
    def extract_dress_list_structure(self, dress_list_df: pd.DataFrame) -> Dict[str, List[str]]:
        """
        Extract the position-based structure from the dress list.
        
        Args:
            dress_list_df: DataFrame containing the dress list
            
        Returns:
            Dictionary with positions as keys and player names as values
        """
        position_players = {}
        
        for column in dress_list_df.columns:
            # Get all non-null values from this column
            players = dress_list_df[column].dropna().astype(str).tolist()
            # Remove empty strings and clean up
            players = [player.strip() for player in players if player.strip() and player.strip().lower() != 'nan']
            
            if players:  # Only add if there are actual players
                position_players[column] = players
                
        return position_players
    
    def similarity_score(self, name1: str, name2: str) -> float:
        """
        Calculate similarity score between two names using SequenceMatcher.
        
        Args:
            name1: First name
            name2: Second name
            
        Returns:
            Similarity score between 0 and 1
        """
        return SequenceMatcher(None, name1.lower(), name2.lower()).ratio()
    
    def find_best_match_traditional(self, dress_name: str, player_info_names: List[str], threshold: float = 0.6) -> Optional[str]:
        """
        Find best match using traditional string similarity as fallback.
        
        Args:
            dress_name: Name from dress list
            player_info_names: List of names from player info
            threshold: Minimum similarity threshold
            
        Returns:
            Best matching name or None if no good match found
        """
        best_match = None
        best_score = 0
        
        for player_name in player_info_names:
            score = self.similarity_score(dress_name, player_name)
            if score > best_score and score >= threshold:
                best_score = score
                best_match = player_name
                
        return best_match
    
    def match_names_with_openai(self, dress_names: List[str], player_info_names: List[str]) -> Dict[str, str]:
        """
        Use OpenAI API to match names between dress list and player info.
        
        Args:
            dress_names: List of names from dress list
            player_info_names: List of names from player info
            
        Returns:
            Dictionary mapping dress list names to player info names
        """
        # Prepare the prompt
        prompt = f"""
You are helping match player names between two lists. The first list contains names from a dress list (which may have nicknames or shortened names), and the second list contains full player names from a player info sheet.

Dress List Names:
{json.dumps(dress_names, indent=2)}

Player Info Names:  
{json.dumps(player_info_names, indent=2)}

Please match each dress list name to the most likely corresponding player info name. Return your response as a JSON object where:
- Keys are the dress list names
- Values are the matching player info names (or null if no good match exists)

Consider that dress list names might be:
- Nicknames (e.g., "Mike" for "Michael")
- Last names only
- Shortened first names
- First name + last name combinations

Only make matches you're confident about. If unsure, return null for that name.

Response format:
{{
  "dress_list_name_1": "matching_player_info_name_1",
  "dress_list_name_2": "matching_player_info_name_2",
  "dress_list_name_3": null
}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert at matching names and understanding name variations, nicknames, and abbreviations."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            
            # Parse the JSON response
            matches_json = response.choices[0].message.content.strip()
            matches = json.loads(matches_json)
            
            return matches
            
        except Exception as e:
            print(f"OpenAI API error: {str(e)}")
            print("Falling back to traditional string matching...")
            
            # Fallback to traditional matching
            matches = {}
            for dress_name in dress_names:
                match = self.find_best_match_traditional(dress_name, player_info_names)
                matches[dress_name] = match
                
            return matches
    
    def organize_player_info(self, dress_list_structure: Dict[str, List[str]], 
                           player_info_df: pd.DataFrame, 
                           name_column: str = None) -> pd.DataFrame:
        """
        Organize player info according to dress list structure.
        
        Args:
            dress_list_structure: Position-based structure from dress list
            player_info_df: DataFrame with player information
            name_column: Column name containing player names (auto-detected if None)
            
        Returns:
            Organized DataFrame matching dress list structure
        """
        # Auto-detect name column if not provided
        if name_column is None:
            possible_name_columns = ['name', 'player_name', 'full_name', 'Name', 'Player Name', 'Full Name']
            for col in possible_name_columns:
                if col in player_info_df.columns:
                    name_column = col
                    break
            
            if name_column is None:
                # Use first column as default
                name_column = player_info_df.columns[0]
                print(f"Warning: Could not auto-detect name column. Using '{name_column}'")
        
        print(f"Using name column: '{name_column}'")
        
        # Get all player names from player info
        all_player_names = player_info_df[name_column].astype(str).tolist()
        
        # Create organized DataFrame
        organized_data = {}
        max_players = 0
        
        for position, dress_names in dress_list_structure.items():
            print(f"\nProcessing position: {position}")
            
            # Match names using OpenAI
            matches = self.match_names_with_openai(dress_names, all_player_names)
            
            # Get player info for matched names - ONLY include successful matches
            position_players = []
            for dress_name in dress_names:
                matched_name = matches.get(dress_name)
                if matched_name:
                    # Find the row with this player
                    player_row = player_info_df[player_info_df[name_column] == matched_name]
                    if not player_row.empty:
                        # Convert to dict and add to list
                        player_data = player_row.iloc[0].to_dict()
                        position_players.append(player_data)
                        print(f"  Matched: {dress_name} -> {matched_name}")
                    else:
                        print(f"  No data found for matched name: {matched_name} (skipping)")
                else:
                    print(f"  No match found for: {dress_name} (skipping)")
            
            # Only add positions that have successfully matched players
            if position_players:
                organized_data[position] = position_players
                max_players = max(max_players, len(position_players))
                print(f"  Added {len(position_players)} players to {position}")
            else:
                print(f"  No matched players for {position}, skipping position")
        
        if not organized_data:
            print("Warning: No positions with matched players found!")
            return pd.DataFrame()
        
        # Create DataFrame with consistent structure
        result_df = pd.DataFrame()
        
        for position, players in organized_data.items():
            # Pad with empty dictionaries if needed to match max_players
            while len(players) < max_players:
                players.append({})
            
            # Create a DataFrame for this position
            position_df = pd.DataFrame(players)
            
            # Add position prefix to column names
            position_df.columns = [f"{position}_{col}" if col else f"{position}_empty_{i}" 
                                 for i, col in enumerate(position_df.columns)]
            
            # Concatenate horizontally
            if result_df.empty:
                result_df = position_df
            else:
                result_df = pd.concat([result_df, position_df], axis=1)
        
        return result_df
    
    def save_organized_roster(self, organized_df: pd.DataFrame, output_path: str):
        """
        Save the organized roster to an Excel file.
        
        Args:
            organized_df: Organized DataFrame
            output_path: Path for output Excel file
        """
        try:
            organized_df.to_excel(output_path, index=False)
            print(f"\nOrganized roster saved to: {output_path}")
        except Exception as e:
            raise Exception(f"Error saving Excel file: {str(e)}")
    
    def process_rosters(self, dress_list_path: str, player_info_path: str, 
                       output_path: str, player_name_column: str = None):
        """
        Main method to process the rosters.
        
        Args:
            dress_list_path: Path to dress list Excel file
            player_info_path: Path to player info Excel file  
            output_path: Path for output Excel file
            player_name_column: Column name with player names in player_info sheet
        """
        print("Loading Excel files...")
        dress_list_df, player_info_df = self.load_excel_files(dress_list_path, player_info_path)
        
        print("Extracting dress list structure...")
        dress_list_structure = self.extract_dress_list_structure(dress_list_df)
        
        print(f"Found positions: {list(dress_list_structure.keys())}")
        
        print("Organizing player information...")
        organized_df = self.organize_player_info(dress_list_structure, player_info_df, player_name_column)
        
        print("Saving organized roster...")
        self.save_organized_roster(organized_df, output_path)
        
        print("Process completed successfully!")

def main():
    """Main function to handle command line arguments."""
    parser = argparse.ArgumentParser(
        description="Organize football player info according to dress list structure",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python roster_organizer.py dress_list.xlsx player_info.xlsx -o organized_roster.xlsx
  python roster_organizer.py dress_list.xlsx player_info.xlsx -o output.xlsx -c "Player Name"
  python roster_organizer.py dress_list.xlsx player_info.xlsx -o output.xlsx --api-key sk-your-key-here
        """
    )
    
    parser.add_argument(
        "dress_list", 
        help="Path to the dress list Excel file"
    )
    
    parser.add_argument(
        "player_info", 
        help="Path to the player info Excel file"
    )
    
    parser.add_argument(
        "-o", "--output",
        default="organized_roster.xlsx",
        help="Output Excel file path (default: organized_roster.xlsx)"
    )
    
    parser.add_argument(
        "-c", "--column",
        help="Column name containing player names in player info sheet (auto-detected if not specified)"
    )
    
    parser.add_argument(
        "--api-key",
        help="OpenAI API key (can also be set via OPENAI_API_KEY environment variable)"
    )
    
    args = parser.parse_args()
    
    # Get API key from argument or environment variable
    api_key = args.api_key or os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("Error: OpenAI API key is required!")
        print("Provide it via --api-key argument or set OPENAI_API_KEY environment variable")
        return 1
    
    # Initialize the organizer
    organizer = FootballRosterOrganizer(api_key)
    
    # Process the rosters
    try:
        print(f"Dress list file: {args.dress_list}")
        print(f"Player info file: {args.player_info}")
        print(f"Output file: {args.output}")
        if args.column:
            print(f"Player name column: {args.column}")
        print()
        
        organizer.process_rosters(
            dress_list_path=args.dress_list,
            player_info_path=args.player_info,
            output_path=args.output,
            player_name_column=args.column
        )
        
        return 0
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1

if __name__ == "__main__":
    exit(main())