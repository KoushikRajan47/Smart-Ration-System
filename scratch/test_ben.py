from services.auth_service import authenticate_user
from database.db import (
    get_beneficiary_monthly_usage,
    get_beneficiary_complaints,
    get_beneficiary_bookings,
    get_connection
)

# 1. Test Auth by username
u1 = authenticate_user("citizen1", "citizenpassword")
assert u1 is not None, "Failed citizen auth"
assert u1["phone"] == "9845033331", f"Expected 9845033331, got {u1.get('phone')}"
print(f"✓ Citizen auth by username verified: {u1['full_name']}, phone: {u1['phone']}")

# 2. Test Auth by Ration Card Number
u2 = authenticate_user("RC-KA-99201", "citizenpassword")
assert u2 is not None, "Failed ration card auth"
assert u2["user_id"] == u1["user_id"]
print(f"✓ Citizen auth by ration card number verified: {u2['ration_card_number']}")

# 3. Test Monthly Usage
usage = get_beneficiary_monthly_usage(u1["beneficiary_id"])
print(f"✓ Monthly usage retrieved: {usage}")

# 4. Test Grievances retrieval
complaints = get_beneficiary_complaints(u1["beneficiary_id"])
print(f"✓ Beneficiary complaints count: {len(complaints)}")

# 5. Test Bookings
bks = get_beneficiary_bookings(u1["beneficiary_id"])
print(f"✓ Beneficiary bookings count: {len(bks)}")

print("\nALL BENEFICIARY BACKEND TESTS PASSED!")

