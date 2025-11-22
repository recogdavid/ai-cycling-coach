from flask import Flask, request, send_file, jsonify
from datetime import datetime, timedelta
import io
import struct

app = Flask(__name__)

class FitFileWriter:
    """Simple FIT file writer for workout files"""
    
    def __init__(self):
        self.messages = []
        
    def create_workout_file(self, workout_data):
        """Create a FIT workout file from workout data"""
        
        # FIT file header
        header = self._create_header()
        
        # File ID message
        file_id = self._create_file_id_message()
        
        # Workout message
        workout_msg = self._create_workout_message(workout_data)
        
        # Workout step messages (intervals)
        steps = self._create_workout_steps(workout_data['intervals'], workout_data['ftp_watts'])
        
        # Combine all parts
        messages = file_id + workout_msg + b''.join(steps)
        
        # Calculate CRC
        crc = self._calculate_crc(header + messages)
        
        # Return complete file
        return header + messages + struct.pack('<H', crc)
    
    def _create_header(self):
        """Create FIT file header"""
        protocol_version = 0x20  # 2.0
        profile_version = 2132  # 21.32
        data_type = b'.FIT'
        
        header = struct.pack(
            '<BHIH4s',
            14,  # header size
            protocol_version,
            profile_version,
            0,  # data_size placeholder
            data_type
        )
        
        # CRC of header
        header_crc = self._calculate_crc(header[:-2])
        return header[:-2] + struct.pack('<H', header_crc)
    
    def _create_file_id_message(self):
        """Create file ID message"""
        # Definition message for file_id (18 bytes total)
        definition = struct.pack(
            '<BBBBBBBBBBBBBBBBBB',  # 18 B's for 18 values
            0x40,  # Definition message with local message type 0
            0,     # Reserved
            0,     # Architecture (little endian)
            0,     # Global message number (file_id) low byte
            0,     # Global message number high byte
            4,     # Number of fields
            3, 4, 0x86,  # Field 0: type (manufacturer)
            4, 4, 0x86,  # Field 1: product
            5, 4, 0x86,  # Field 2: serial number
            1, 4, 0x86   # Field 3: time_created
        )
        
        # Data message
        timestamp = int((datetime.now() - datetime(1989, 12, 31)).total_seconds())
        data = struct.pack(
            '<BIIII',
            0x00,  # Data message with local message type 0
            4,     # type = 4 (workout)
            0xFFFF,  # product = unknown
            0xFFFFFFFF,  # serial = unknown
            timestamp
        )
        
        return definition + data
    
    def _create_workout_message(self, workout_data):
        """Create workout message"""
        # Definition message for workout (12 bytes total)
        definition = struct.pack(
            '<BBBBBBBBBBBB',  # 12 B's for 12 values
            0x41,  # Definition with local message type 1
            0,     # Reserved
            0,     # Architecture
            26,    # Global message number (workout) low byte
            0,     # Global message number high byte
            2,     # Number of fields (2 fields)
            8, 16, 0x07,  # Field 0: wkt_name (string, 16 bytes)
            11, 1, 0x00   # Field 1: num_valid_steps (uint8)
        )
        
        workout_name = workout_data.get('name', 'Workout')[:15].encode('utf-8').ljust(16, b'\x00')
        num_steps = len(workout_data['intervals'])
        
        data = struct.pack('<B', 0x01) + workout_name + struct.pack('<B', num_steps)
        
        return definition + data
    
    def _create_workout_steps(self, intervals, ftp_watts):
        """Create workout step messages from intervals"""
        steps = []
        
        # Step definition message (23 bytes total)
        step_def = struct.pack(
            '<BBBBBBBBBBBBBBBBBBBBBBBB',  # 23 B's for 23 values
            0x42,  # Definition with local message type 2
            0,     # Reserved
            0,     # Architecture
            27,    # Global message number (workout_step) low byte
            0,     # Global message number high byte
            6,     # Number of fields (6 fields)
            254, 2, 0x84,  # Field 0: message_index (uint16)
            0, 16, 0x07,   # Field 1: wkt_step_name (string, 16 bytes)
            1, 1, 0x00,    # Field 2: duration_type (enum)
            2, 4, 0x86,    # Field 3: duration_value (uint32)
            3, 1, 0x00,    # Field 4: target_type (enum)
            4, 4, 0x86     # Field 5: target_value (uint32)
        )
        
        steps.append(step_def)
        
        for idx, interval in enumerate(intervals):
            step_name = interval.get('type', 'interval')[:15].encode('utf-8').ljust(16, b'\x00')
            duration = int(interval['duration'])  # seconds
            
            # Calculate target power in watts
            power_pct = interval.get('power_pct', 70)
            target_power = int(ftp_watts * (power_pct / 100))
            
            # Data message
            step_data = struct.pack(
                '<BH',
                0x02,  # Data message with local message type 2
                idx
            ) + step_name + struct.pack(
                '<BIBI',
                0,  # duration_type = time
                duration * 1000,  # duration in ms
                1,  # target_type = power
                target_power
            )
            
            steps.append(step_data)
        
        return steps
    
    def _calculate_crc(self, data):
        """Calculate CRC-16 for FIT files"""
        crc_table = [
            0x0000, 0xCC01, 0xD801, 0x1400, 0xF001, 0x3C00, 0x2800, 0xE401,
            0xA001, 0x6C00, 0x7800, 0xB401, 0x5000, 0x9C01, 0x8801, 0x4400
        ]
        
        crc = 0
        for byte in data:
            tmp = crc_table[crc & 0xF]
            crc = (crc >> 4) & 0x0FFF
            crc = crc ^ tmp ^ crc_table[byte & 0xF]
            
            tmp = crc_table[crc & 0xF]
            crc = (crc >> 4) & 0x0FFF
            crc = crc ^ tmp ^ crc_table[(byte >> 4) & 0xF]
        
        return crc

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy"}), 200

@app.route('/generate-fit', methods=['POST'])
def generate_fit():
    """Generate FIT file from workout data"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required = ['name', 'intervals', 'ftp_watts']
        for field in required:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Generate FIT file
        writer = FitFileWriter()
        fit_data = writer.create_workout_file(data)
        
        # Create filename
        filename = data.get('filename', 'workout.fit')
        if not filename.endswith('.fit'):
            filename += '.fit'
        
        # Return as file
        return send_file(
            io.BytesIO(fit_data),
            mimetype='application/octet-stream',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
