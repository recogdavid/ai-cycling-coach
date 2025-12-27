from flask import Flask, request, send_file, jsonify
from datetime import datetime
import io
import struct
import json

app = Flask(__name__)

def create_valid_fit_file(workout_data):
    """
    Create a minimal but valid FIT workout file
    Based on FIT SDK specification
    """
    
    # Get workout data
    workout_name = workout_data.get('name', 'Workout')[:15]
    intervals = workout_data.get('intervals', [])
    ftp = workout_data.get('ftp_watts', 250)
    
    print(f"Creating FIT for: {workout_name}, {len(intervals)} intervals")
    
    # If no intervals, create a simple one
    if not intervals:
        intervals = [{
            'name': 'Steady',
            'duration': '30 min',
            'target_power': {'percentage_ftp': '70% FTP'}
        }]
    
    # ===== 1. CREATE MESSAGES =====
    messages = bytearray()
    
    # ----- File ID Message (Local Message Type 0) -----
    # Definition Message
    messages.extend([
        0x40, 0x00, 0x00,       # Header: definition, reserved, arch (little)
        0x00, 0x00,             # Global message number: file_id (0)
        0x04,                   # Number of fields: 4
        
        # Field 0: type (uint32)
        0x03, 0x04, 0x86,
        # Field 1: product (uint32)
        0x04, 0x04, 0x86,
        # Field 2: serial_number (uint32)
        0x05, 0x04, 0x86,
        # Field 3: time_created (uint32)
        0x01, 0x04, 0x86
    ])
    
    # Data Message
    timestamp = int((datetime.now() - datetime(1989, 12, 31)).total_seconds())
    messages.extend([
        0x00,                   # Header: data, local type 0
        0x04, 0x00, 0x00, 0x00, # type = workout (4)
        0xFF, 0xFF, 0x00, 0x00, # product = 65535 (unknown)
        0xFF, 0xFF, 0xFF, 0xFF, # serial = 4294967295 (unknown)
        timestamp & 0xFF, (timestamp >> 8) & 0xFF,
        (timestamp >> 16) & 0xFF, (timestamp >> 24) & 0xFF
    ])
    
    # ----- Workout Message (Local Message Type 1) -----
    # Definition Message
    messages.extend([
        0x41, 0x00, 0x00,       # Header: definition, reserved, arch
        0x1A, 0x00,             # Global message number: workout (26)
        0x02,                   # Number of fields: 2
        
        # Field 0: wkt_name (string, 16 bytes)
        0x08, 0x10, 0x07,
        # Field 1: num_valid_steps (uint8)
        0x0B, 0x01, 0x00
    ])
    
    # Data Message
    workout_name_bytes = workout_name.encode('utf-8')[:15].ljust(16, b'\x00')
    messages.extend([
        0x01,                   # Header: data, local type 1
        *workout_name_bytes,    # wkt_name (16 bytes)
        len(intervals) & 0xFF   # num_valid_steps
    ])
    
    # ----- Workout Step Messages (Local Message Type 2) -----
    if intervals:
        # Definition Message (only once)
        messages.extend([
            0x42, 0x00, 0x00,   # Header: definition, reserved, arch
            0x1B, 0x00,         # Global message number: workout_step (27)
            0x06,               # Number of fields: 6
            
            # Field 0: message_index (uint16)
            0xFE, 0x02, 0x84,
            # Field 1: wkt_step_name (string, 16 bytes)
            0x00, 0x10, 0x07,
            # Field 2: duration_type (enum)
            0x01, 0x01, 0x00,
            # Field 3: duration_value (uint32)
            0x02, 0x04, 0x86,
            # Field 4: target_type (enum)
            0x03, 0x01, 0x00,
            # Field 5: target_value (uint32)
            0x04, 0x04, 0x86
        ])
        
        # Data Messages (one per interval)
        for idx, interval in enumerate(intervals):
            # Get step name
            step_name = interval.get('name', interval.get('type', f'Step {idx+1}'))
            step_name_bytes = step_name.encode('utf-8')[:15].ljust(16, b'\x00')
            
            # Get duration in milliseconds
            duration_str = interval.get('duration', '0')
            if 'min' in duration_str:
                duration_sec = int(float(duration_str.replace('min', '').strip()) * 60)
            else:
                duration_sec = int(duration_str)
            duration_ms = duration_sec * 1000
            
            # Get target power
            target_power = 150
            if 'target_power' in interval and isinstance(interval['target_power'], dict):
                power_str = interval['target_power'].get('percentage_ftp', '70% FTP')
                try:
                    power_pct = float(power_str.replace('% FTP', '').strip())
                    target_power = int(ftp * (power_pct / 100))
                except:
                    pass
            
            # Build step data
            messages.extend([
                0x02,                       # Header: data, local type 2
                idx & 0xFF, (idx >> 8) & 0xFF,  # message_index
                *step_name_bytes,           # wkt_step_name (16 bytes)
                0x00,                       # duration_type = time (0)
                duration_ms & 0xFF, (duration_ms >> 8) & 0xFF,
                (duration_ms >> 16) & 0xFF, (duration_ms >> 24) & 0xFF,
                0x01,                       # target_type = power (1)
                target_power & 0xFF, (target_power >> 8) & 0xFF,
                (target_power >> 16) & 0xFF, (target_power >> 24) & 0xFF
            ])
    
    # ===== 2. CREATE HEADER =====
    data_size = len(messages)
    header = bytearray([
        0x0E,                   # Header size (14)
        0x20,                   # Protocol version (2.0)
        0x54, 0x08,             # Profile version (2132)
        data_size & 0xFF, (data_size >> 8) & 0xFF,
        (data_size >> 16) & 0xFF, (data_size >> 24) & 0xFF,
        0x2E, 0x46, 0x49, 0x54, # ".FIT"
        0x00, 0x00              # CRC placeholder
    ])
    
    # Calculate header CRC (CRC of first 12 bytes)
    header_crc = calculate_crc(bytes(header[:12]))
    header[12] = header_crc & 0xFF
    header[13] = (header_crc >> 8) & 0xFF
    
    # ===== 3. CALCULATE FILE CRC =====
    file_data = bytes(header) + bytes(messages)
    file_crc = calculate_crc(file_data)
    
    # ===== 4. RETURN COMPLETE FILE =====
    return file_data + struct.pack('<H', file_crc)

def calculate_crc(data):
    """Calculate FIT CRC-16"""
    crc_table = [
        0x0000, 0xCC01, 0xD801, 0x1400, 0xF001, 0x3C00, 0x2800, 0xE401,
        0xA001, 0x6C00, 0x7800, 0xB401, 0x5000, 0x9C01, 0x8801, 0x4400
    ]
    
    crc = 0
    for byte in data:
        # Process lower nibble
        tmp = crc_table[crc & 0xF]
        crc = (crc >> 4) & 0x0FFF
        crc = crc ^ tmp ^ crc_table[byte & 0xF]
        
        # Process upper nibble
        tmp = crc_table[crc & 0xF]
        crc = (crc >> 4) & 0x0FFF
        crc = crc ^ tmp ^ crc_table[(byte >> 4) & 0xF]
    
    return crc

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"}), 200

@app.route('/test-simple', methods=['GET'])
def test_simple():
    """Test endpoint with hardcoded data"""
    test_data = {
        'name': 'Test Workout',
        'ftp_watts': 250,
        'intervals': [
            {
                'name': 'Warmup',
                'duration': '10 min',
                'target_power': {'percentage_ftp': '60% FTP'}
            },
            {
                'name': 'Main',
                'duration': '20 min',
                'target_power': {'percentage_ftp': '85% FTP'}
            }
        ]
    }
    
    fit_data = create_valid_fit_file(test_data)
    print(f"Test FIT size: {len(fit_data)} bytes")
    
    # Debug: show first 32 bytes
    print("First 32 bytes (hex):", fit_data[:32].hex())
    
    return send_file(
        io.BytesIO(fit_data),
        mimetype='application/octet-stream',
        as_attachment=True,
        download_name='test_simple.fit'
    )

@app.route('/generate-fit', methods=['POST'])
def generate_fit():
    """Generate FIT file from workout data"""
    try:
        data = request.get_json()
        
        print("=" * 60)
        print("GENERATING FIT FILE")
        print(f"Name: {data.get('name')}")
        print(f"FTP: {data.get('ftp_watts')}")
        print(f"Intervals count: {len(data.get('intervals', []))}")
        
        if data.get('intervals'):
            print("First interval:", json.dumps(data['intervals'][0], indent=2))
        
        # Generate FIT file
        fit_data = create_valid_fit_file(data)
        
        print(f"FIT file size: {len(fit_data)} bytes")
        print("First 16 bytes (hex):", fit_data[:16].hex())
        print("=" * 60)
        
        # Create filename
        filename = data.get('filename', 'workout.fit')
        if not filename.endswith('.fit'):
            filename += '.fit'
        
        return send_file(
            io.BytesIO(fit_data),
            mimetype='application/octet-stream',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
