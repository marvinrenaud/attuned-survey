# Subscription Implementation Guide V1

## Overview

This guide provides step-by-step instructions for implementing subscription features in the Attuned FlutterFlow app. This includes promo code validation, RevenueCat integration, subscription status syncing, and subscription management UI.

**What You'll Build:**

- **Promo Code System**: Validate promo codes against backend, display discounted pricing
- **RevenueCat Purchase Flow**: Integrated payment flow (RevenueCat handles US/non-US routing automatically)
- **Subscription Status Sync**: Fetch and cache subscription state on app launch and after purchases
- **Subscription Management**: View/manage subscription status in Settings

**Prerequisites:**
- RevenueCat is already enabled in FlutterFlow (Settings > In-App Purchases & Subscriptions)
- RevenueCat products/offerings are configured (Monthly: $4.99, Annual: $29.99)
- Backend subscription APIs are deployed

**Scope Exclusions (handled by backend or deferred):**
- Activity limit enforcement (backend handles via game API)
- Region detection (RevenueCat Web Purchase Button handles automatically)
- Billing issue banners (deferred to post-MVP)

---

## Section 1: Data Types & App State (Foundation)

This section creates the foundational data structures and state management variables.

### 1.1: Update SubscriptionStatusStruct Data Type

The existing `SubscriptionStatusStruct` needs to be updated to match the new API response format.

- [ ] **1.1.1** - From the left navigation menu, go to **Data Representation > Data Types**.

- [ ] **1.1.2** - Find and select `SubscriptionStatusStruct` in the list.

- [ ] **1.1.3** - Update the existing fields and add new fields to match this structure:

| Field Name | Type | Is List | Nullable | Notes |
|------------|------|---------|----------|-------|
| `user_id` | `String` | No | Yes | Keep existing |
| `subscription_tier` | `String` | No | Yes | Keep existing ("premium" or "free") |
| `is_premium` | `Boolean` | No | Yes | Keep existing |
| `expires_at` | `String` | No | Yes | Keep existing (ISO timestamp) |
| `is_cancelled` | `Boolean` | No | Yes | **NEW** - Whether subscription is cancelled |
| `platform` | `String` | No | Yes | **NEW** - "stripe", "apple", or "google" |
| `product_id` | `String` | No | Yes | **NEW** - RevenueCat product identifier |
| `activities_used` | `Integer` | No | Yes | **NEW** - Replaces daily_activity_count |
| `activities_limit` | `Integer` | No | Yes | **NEW** - Lifetime limit (10 for free) |
| `activities_remaining` | `Integer` | No | Yes | **NEW** - Remaining activities |
| `has_billing_issue` | `Boolean` | No | Yes | **NEW** - Payment problem flag |
| `promo_code_used` | `String` | No | Yes | **NEW** - Applied promo code |

- [ ] **1.1.4** - **Remove** the following deprecated fields (if they exist):
  - `daily_activity_count`
  - `daily_activity_reset_at`

- [ ] **1.1.5** - Click **Save**.

> **Note**: Removing old fields may cause compile errors in existing code. FlutterFlow will highlight these - they'll need to be updated to use new fields.

### 1.2: Create PromoValidationResponseStruct Data Type

- [ ] **1.2.1** - Click the **+ (plus)** icon and select **Create Data Type**.

- [ ] **1.2.2** - Name the Data Type: `PromoValidationResponseStruct`.

- [ ] **1.2.3** - Add the following fields:

| Field Name | Type | Is List | Nullable | Notes |
|------------|------|---------|----------|-------|
| `valid` | `Boolean` | No | No | Whether code is valid |
| `code` | `String` | No | Yes | The promo code string |
| `discount_percent` | `Integer` | No | Yes | Discount percentage (e.g., 20) |
| `influencer_name` | `String` | No | Yes | Associated influencer name |
| `offering_id` | `String` | No | Yes | RevenueCat offering ID to use |
| `error` | `String` | No | Yes | Error message if invalid |

- [ ] **1.2.4** - Click **Save**.

### 1.3: Create App State Variables

- [ ] **1.3.1** - Go to **App State** (left navigation menu).

- [ ] **1.3.2** - Create the following new App State variables:

| Variable Name | Type | Is List | Persisted | Initial Value | Notes |
|---------------|------|---------|-----------|---------------|-------|
| `isPremium` | `Boolean` | No | No | `false` | Quick access premium flag |
| `subscriptionStatus` | `SubscriptionStatusStruct` | No | No | (Unset) | Full subscription state |
| `activitiesRemaining` | `Integer` | No | No | `10` | For free tier display |
| `appliedPromoCode` | `String` | No | No | `""` | Currently applied promo |
| `appliedOfferingId` | `String` | No | No | `"default"` | RC offering to use for purchase |
| `subscriptionEntryPoint` | `String` | No | No | `""` | Track where user came from |

- [ ] **1.3.3** - Click **Save** after adding all variables.

> **Architectural Note**: `subscriptionStatus` holds the complete state from the API. `isPremium` and `activitiesRemaining` provide quick access for conditional UI without navigating nested objects.

---

## Section 2: API Calls

This section creates the API call definitions for subscription endpoints.

### 2.1: Navigate to API Calls

- [ ] **2.1.1** - From the left navigation menu, go to **Backend & API > API Calls**.

- [ ] **2.1.2** - You should see your existing API Group (likely `PartnerAPIGroup`). We'll add new calls to this group.

### 2.2: Create validatePromoCode API Call

- [ ] **2.2.1** - Click **+ Add** and select **Create API Call**.

- [ ] **2.2.2** - In the **Definition** tab, configure:
  - **API Call Name**: `validatePromoCode`
  - **Method Type**: `POST`
  - **API URL**: `https://attuned-backend.onrender.com/api/promo/validate`

- [ ] **2.2.3** - In the **Headers** section, add:

| Header Name | Header Value |
|-------------|--------------|
| `Content-Type` | `application/json` |
| `Authorization` | `Bearer [authToken]` |

- [ ] **2.2.4** - In the **Variables** section, add:

| Variable Name | Type | Is List | Default Value |
|---------------|------|---------|---------------|
| `authToken` | `String` | No | |
| `code` | `String` | No | |

- [ ] **2.2.5** - In the **Body** tab, select **JSON** and set:

```json
{
  "code": "<code>"
}
```

- [ ] **2.2.6** - In the **Response & Test** tab:
  - Set test values: `code` = `TEST` (or a valid code if known)
  - Set `authToken` to a valid JWT
  - Click **Test API Call**

- [ ] **2.2.7** - After testing, enable **Parse as Data Type** and select `PromoValidationResponseStruct`.

- [ ] **2.2.8** - Click **Add Call**.

### 2.3: Create getSubscriptionStatus API Call

- [ ] **2.3.1** - Create a new API call named `getSubscriptionStatus`.

- [ ] **2.3.2** - In the **Definition** tab, configure:
  - **Method Type**: `GET`
  - **API URL**: `https://attuned-backend.onrender.com/api/subscriptions/status/<userId>`

- [ ] **2.3.3** - In the **Headers** section, add:

| Header Name | Header Value |
|-------------|--------------|
| `Authorization` | `Bearer [authToken]` |

- [ ] **2.3.4** - In the **Variables** section, add:

| Variable Name | Type | Is List | Default Value |
|---------------|------|---------|---------------|
| `authToken` | `String` | No | |
| `userId` | `String` | No | |

- [ ] **2.3.5** - In the **Response & Test** tab, test with valid credentials.

- [ ] **2.3.6** - Enable **Parse as Data Type** and select `SubscriptionStatusStruct`.

- [ ] **2.3.7** - Click **Add Call**.

---

## Section 3: RevenueCat Configuration

RevenueCat is already enabled. This section covers additional configuration for the subscription flow.

### 3.1: Verify RevenueCat Setup

- [ ] **3.1.1** - Go to **Settings** (gear icon) > **In-App Purchases & Subscriptions**.

- [ ] **3.1.2** - Verify the following are configured:
  - **Enable RevenueCat**: ON
  - **iOS API Key**: Set (from RevenueCat dashboard)
  - **Android API Key**: Set (from RevenueCat dashboard)

- [ ] **3.1.3** - Note the **Entitlement Identifier** configured (likely `premium` or similar).

> **Important**: The entitlement identifier must match what's configured in RevenueCat dashboard.

### 3.2: Configure User Identification

RevenueCat needs to identify users by their Supabase auth UUID.

- [ ] **3.2.1** - This is typically handled automatically when purchasing. Verify that on login, you're calling RevenueCat's `logIn` method with the user ID.

- [ ] **3.2.2** - If not already configured, you'll add this in Section 4 (Subscription Status Sync).

### 3.3: Verify RevenueCat Offerings

In the RevenueCat dashboard (external to FlutterFlow):

- [ ] **3.3.1** - Verify a `default` offering exists with:
  - Monthly package ($4.99)
  - Annual package ($29.99)

- [ ] **3.3.2** - Create a `discounted_20_percent` offering (for promo codes) with:
  - Monthly package ($3.99)
  - Annual package ($23.99)

> **Note**: Promo code validation returns the `offering_id` to use. The app passes this to RevenueCat's purchase flow.

---

## Section 4: Subscription Status Sync

This section implements syncing subscription status on app launch and after purchases.

### 4.1: Add Sync on App Launch (SplashPage)

The subscription status should be fetched after successful login.

- [ ] **4.1.1** - Navigate to **SplashPage** in the widget tree.

- [ ] **4.1.2** - Select the page and go to **Actions** > **On Page Load**.

- [ ] **4.1.3** - Find where the login/authentication check occurs. After confirming user is logged in, add the following actions:

#### Action Sequence: Sync Subscription Status

- [ ] **4.1.3.1** - **Add Conditional Action**:
  - **Condition**: `Authenticated User > uid` → `Is Set`

- [ ] **4.1.3.2** - Inside the **TRUE** branch, add **Execute API Call** → `getSubscriptionStatus`:
  - **Variables**:
    - `authToken`: `Authenticated User > Auth Token`
    - `userId`: `Authenticated User > uid`
  - **Action Output Variable Name**: `subscriptionResponse`

- [ ] **4.1.3.3** - Add **Conditional Action**:
  - **Condition**: `subscriptionResponse` → `Succeeded` → `Equal To` → `True`

- [ ] **4.1.3.4** - Inside the **TRUE** branch, add **Update App State**:
  - **Field**: `subscriptionStatus`
  - **Value**: `subscriptionResponse` (the parsed struct)

- [ ] **4.1.3.5** - Add another **Update App State**:
  - **Field**: `isPremium`
  - **Value**: `subscriptionResponse > is_premium`

- [ ] **4.1.3.6** - Add another **Update App State**:
  - **Field**: `activitiesRemaining`
  - **Value**: `subscriptionResponse > activities_remaining`

> **Tip**: Place these actions after the user profile fetch but before navigating to the main app.

### 4.2: Create Reusable Custom Action for Sync

To avoid duplicating the sync logic, create a Custom Action.

- [ ] **4.2.1** - Go to **Custom Code** > **Custom Actions**.

- [ ] **4.2.2** - Click **+ Add** > **Create New Action**.

- [ ] **4.2.3** - Name it: `syncSubscriptionStatus`.

- [ ] **4.2.4** - Add the following code:

```dart
// Automatic FlutterFlow imports
import '/backend/api_requests/api_calls.dart';
import '/backend/schema/structs/index.dart';
import '/flutter_flow/flutter_flow_util.dart';
import 'package:flutter/material.dart';

Future syncSubscriptionStatus(BuildContext context) async {
  // Get current user
  final currentUser = currentUserUid;
  final authToken = currentJwtToken;

  if (currentUser == null || currentUser.isEmpty) {
    return; // Not logged in
  }

  if (authToken == null || authToken.isEmpty) {
    return; // No auth token
  }

  try {
    // Call the subscription status API
    final response = await PartnerAPIGroup.getSubscriptionStatusCall.call(
      authToken: authToken,
      userId: currentUser,
    );

    if (response.succeeded) {
      final statusData = response.jsonBody;

      // Parse the response into struct
      final subscriptionStatus = SubscriptionStatusStruct.fromMap(
        statusData as Map<String, dynamic>
      );

      // Update App State
      FFAppState().update(() {
        FFAppState().subscriptionStatus = subscriptionStatus;
        FFAppState().isPremium = subscriptionStatus.isPremium;
        FFAppState().activitiesRemaining = subscriptionStatus.activitiesRemaining;
      });
    }
  } catch (e) {
    // Log error but don't block app flow
    debugPrint('Error syncing subscription status: $e');
  }
}
```

- [ ] **4.2.5** - Click **Save**.

> **Note**: This custom action can be called from multiple places (splash page, after purchase, settings page).

### 4.3: Alternative - Use Action Flow Editor

If you prefer not to use custom code, implement the sync using the Action Flow Editor as described in 4.1.

---

## Section 5: Paywall Page Updates (SubscriptionIntroPage)

This section adds promo code input and updates the purchase flow on the existing SubscriptionIntroPage.

### 5.1: Add Page State Variables

- [ ] **5.1.1** - Select **SubscriptionIntroPage** in the widget tree.

- [ ] **5.1.2** - In the Properties Panel, go to **Page State**.

- [ ] **5.1.3** - Add the following Page State variables:

| Variable Name | Type | Initial Value | Nullable |
|---------------|------|---------------|----------|
| `promoCode` | `String` | `""` | No |
| `promoApplied` | `Boolean` | `false` | No |
| `promoError` | `String` | `""` | No |
| `isValidatingPromo` | `Boolean` | `false` | No |
| `discountPercent` | `Integer` | `0` | No |
| `selectedPlan` | `String` | `""` | No |

### 5.2: Set Entry Point on Page Load

Track where the user came from for post-purchase navigation.

- [ ] **5.2.1** - Select **SubscriptionIntroPage**.

- [ ] **5.2.2** - Go to **Actions** > **On Page Load**.

- [ ] **5.2.3** - Add **Update App State**:
  - **Field**: `subscriptionEntryPoint`
  - **Value**: (Set based on how user arrived - this may require a page parameter)

> **Alternative**: Add a page parameter `entryPoint` (String) to SubscriptionIntroPage and pass it when navigating to this page.

### 5.3: Add Promo Code Input Section

Add a text field and button for promo code validation below the feature list.

- [ ] **5.3.1** - In the widget tree, find the **Column** containing the feature items.

- [ ] **5.3.2** - Add a new **Container** below the feature items (before subscription options):

**Container Properties:**
- **Width**: `double.infinity`
- **Padding**: 16 (all sides)
- **Background Color**: `transparent`

- [ ] **5.3.3** - Inside the Container, add a **Row**:

**Row Properties:**
- **Main Axis Alignment**: `Start`
- **Cross Axis Alignment**: `Center`

- [ ] **5.3.4** - Inside the Row, add:

**5.3.4.1 - TextField:**
- **Width**: Expanded (use Expanded wrapper)
- **Controller**: Create a new controller named `promoCodeController`
- **Hint Text**: `"Enter promo code"`
- **Border Radius**: 8
- **Enabled**: Bind to `NOT(isValidatingPromo)`

**5.3.4.2 - Spacer**: Width 8

**5.3.4.3 - Button:**
- **Text**: Conditional → If `isValidatingPromo` then `"..."` else `"Apply"`
- **Width**: 80
- **On Tap**: (Configure in 5.4)

### 5.4: Configure Promo Code Validation Action

- [ ] **5.4.1** - Select the "Apply" button.

- [ ] **5.4.2** - Go to **Actions** > **On Tap** > **Add Action**.

- [ ] **5.4.3** - Configure the action sequence:

**Action 1: Update Page State**
- **Field**: `isValidatingPromo`
- **Value**: `true`

**Action 2: Update Page State**
- **Field**: `promoError`
- **Value**: `""`

**Action 3: Execute API Call** → `validatePromoCode`
- **Variables**:
  - `authToken`: `Authenticated User > Auth Token`
  - `code`: `Page State > promoCode` (or `promoCodeController.text`)
- **Action Output Variable Name**: `promoResponse`

**Action 4: Conditional Action**
- **Condition**: `promoResponse > Succeeded` AND `promoResponse > valid` → `Equal To` → `True`

**Inside TRUE branch:**

**Action 4a: Update Page State**
- **Field**: `promoApplied`
- **Value**: `true`

**Action 4b: Update Page State**
- **Field**: `discountPercent`
- **Value**: `promoResponse > discount_percent`

**Action 4c: Update App State**
- **Field**: `appliedPromoCode`
- **Value**: `promoResponse > code`

**Action 4d: Update App State**
- **Field**: `appliedOfferingId`
- **Value**: `promoResponse > offering_id`

**Inside FALSE branch:**

**Action 4e: Update Page State**
- **Field**: `promoError`
- **Value**: `promoResponse > error` (or default: `"Invalid promo code"`)

**Action 4f: Update Page State**
- **Field**: `promoApplied`
- **Value**: `false`

**Action 5: Update Page State**
- **Field**: `isValidatingPromo`
- **Value**: `false`

### 5.5: Add Promo Feedback Display

- [ ] **5.5.1** - Below the promo input Row, add a **Conditional Builder**:

**Condition 1**: `promoApplied` → `Equal To` → `True`

**Inside TRUE (Success):**
- Add a **Row** with:
  - **Icon**: Check circle (green)
  - **Text**: `"Promo applied: [discountPercent]% off!"` (use string interpolation)
  - **Text Color**: Success green

**Condition 2 (Else-If)**: `promoError` → `Is Set` AND `promoError` → `Not Equal To` → `""`

**Inside TRUE (Error):**
- Add a **Row** with:
  - **Icon**: Error (red)
  - **Text**: `Page State > promoError`
  - **Text Color**: Error red

### 5.6: Update Subscription Option Components

The existing `SubscriptionOptionWidget` components need to show discounted pricing when a promo is applied.

- [ ] **5.6.1** - Update the **Annual** subscription option:

Current:
```
subscriptionPriceMessage: 'Intimacy all year: $29.99'
```

Change to use **Conditional Value**:
- **Condition**: `Page State > promoApplied` → `Equal To` → `True`
- **TRUE**: `"Intimacy all year: $23.99 (was $29.99)"`
- **FALSE**: `"Intimacy all year: $29.99"`

- [ ] **5.6.2** - Update the **Monthly** subscription option:

Change to use **Conditional Value**:
- **Condition**: `Page State > promoApplied` → `Equal To` → `True`
- **TRUE**: `"Intimacy all month: $3.99 (was $4.99)"`
- **FALSE**: `"Intimacy all month: $4.99"`

### 5.7: Add On Tap Actions to Subscription Options

Currently the subscription options don't have actions. Add purchase triggers.

- [ ] **5.7.1** - Select the **Annual** subscription option component.

- [ ] **5.7.2** - Add **On Tap** action:

**Action 1: Update Page State**
- **Field**: `selectedPlan`
- **Value**: `"annual"`

**Action 2: RevenueCat - Purchase Package**
- **Offering ID**: `App State > appliedOfferingId` (defaults to "default")
- **Package Type**: `Annual`

**Action 3: (On Success) - See Section 6**

- [ ] **5.7.3** - Repeat for **Monthly** subscription option with:
- **Package Type**: `Monthly`
- `selectedPlan`: `"monthly"`

---

## Section 6: Payment Flow Implementation

This section implements the purchase flow using RevenueCat's built-in actions.

### 6.1: Understanding RevenueCat Purchase Flow

RevenueCat handles the complexity of:
- Detecting user region (US vs non-US)
- Showing appropriate payment UI (Web Purchase Button for US, native IAP for others)
- Processing payments via Stripe (US) or App Store/Play Store
- Syncing entitlements

**Your job**: Call the purchase action and handle success/failure.

### 6.2: Configure Purchase Action on Annual Option

- [ ] **6.2.1** - Select the **Annual** subscription option.

- [ ] **6.2.2** - Go to **Actions** > **On Tap** (you may have started this in 5.7).

- [ ] **6.2.3** - Configure the complete action sequence:

**Action 1: Log Firebase Event**
- **Event Name**: `purchase_initiated`
- **Parameters**: `plan: annual, promo: [appliedPromoCode]`

**Action 2: RevenueCat - Purchase**
- **Action Type**: `Purchases - Purchase Package`
- **Offering Identifier**: `App State > appliedOfferingId`
- **Package Type**: `Annual`
- **Action Output Variable Name**: `purchaseResult`

**Action 3: Conditional Action** (Check for success)
- **Condition**: `purchaseResult > Succeeded` → `Equal To` → `True`

**Inside TRUE branch (Purchase Successful):**

**Action 3a: Log Firebase Event**
- **Event Name**: `purchase_completed`
- **Parameters**: `plan: annual, promo: [appliedPromoCode]`

**Action 3b: Custom Action** → `syncSubscriptionStatus`
- (This refreshes the subscription state from backend)

**Action 3c: Update App State**
- **Field**: `isPremium`
- **Value**: `true`

**Action 3d: Show Snack Bar** (or custom dialog)
- **Message**: `"Welcome to Premium! You now have unlimited activities."`
- **Duration**: 3 seconds

**Action 3e: Navigate Back**
- Use `context.pop()` or navigate to entry point:
  - If `App State > subscriptionEntryPoint` is set, navigate there
  - Otherwise, navigate to **TapToPlay**

**Inside FALSE branch (Purchase Failed/Cancelled):**

**Action 3f: Conditional Action**
- **Condition**: `purchaseResult > Error Message` → `Is Set`

**Action 3f-TRUE: Show Snack Bar**
- **Message**: `purchaseResult > Error Message`
- **Background Color**: Error color

**Action 3f-FALSE**: (User cancelled - no action needed)

### 6.3: Configure Purchase Action on Monthly Option

- [ ] **6.3.1** - Repeat the same action sequence for the **Monthly** option.

- [ ] **6.3.2** - Only differences:
  - **Package Type**: `Monthly`
  - **Firebase event parameters**: `plan: monthly`

### 6.4: Alternative - Create Success Modal Component

If you prefer a modal over a snack bar:

- [ ] **6.4.1** - Create a new component: `PurchaseSuccessModal`.

- [ ] **6.4.2** - Design with:
  - Success icon (checkmark or heart)
  - Headline: "Welcome to Premium!"
  - Body: "You now have unlimited activities to explore with your partner."
  - Button: "Let's Go!" → Dismiss and navigate

- [ ] **6.4.3** - In the purchase success flow, replace Snack Bar with:
  - **Show Bottom Sheet** → `PurchaseSuccessModal`

---

## Section 7: Subscription Management UI

This section adds subscription viewing/management to the Settings page.

### 7.1: Add Subscription Item to Settings Page

- [ ] **7.1.1** - Navigate to **SettingsPage** in the widget tree.

- [ ] **7.1.2** - Find the Container with the credentials settings (Password Reset, Email Reset).

- [ ] **7.1.3** - Add a new Container section above or below it for Subscription:

**Container Properties:**
- **Width**: `double.infinity`
- **Background Color**: `secondaryBackground`
- **Border Radius**: 16
- **Border**: 1px, `accent4`

- [ ] **7.1.4** - Inside the Container, add a `SettingsListItemWidget`:

```
icon: Icon(FFIcons.kcrown) // or similar premium icon
title: 'Subscription'
valueText: Conditional → If isPremium then 'Premium' else 'Free'
showChevron: true
showToggle: false
onTap: [Navigate to SubscriptionManagementPage or show bottom sheet]
```

### 7.2: Create SubscriptionManagementPage (Optional)

For a dedicated management page:

- [ ] **7.2.1** - Create a new page: `SubscriptionManagementPage`.

- [ ] **7.2.2** - Add route: `/subscriptionManagement`.

- [ ] **7.2.3** - Add `requireAuth: true`.

- [ ] **7.2.4** - Build the page structure:

**7.2.4.1 - TitleAppBar:**
- **pageTitle**: `"Subscription"`
- **showBackButton**: `true`

**7.2.4.2 - Conditional Builder:**
- **Condition**: `App State > isPremium` → `Equal To` → `True`

**TRUE (Premium User):**

- **Container** with premium styling:
  - Crown icon or premium badge
  - Text: "Premium Member"
  - Text: Current plan (from `subscriptionStatus > product_id`)
  - Text: Conditional:
    - If `subscriptionStatus > is_cancelled`: `"Access until: [expires_at formatted]"`
    - Else: `"Renews: [expires_at formatted]"`

- **Button**: "Manage Subscription"
  - **On Tap**: Open URL → RevenueCat Management URL or platform-specific:
    - iOS: `"https://apps.apple.com/account/subscriptions"`
    - Android: `"https://play.google.com/store/account/subscriptions"`

**FALSE (Free User):**

- **Container**:
  - Text: "Free Plan"
  - Text: `"Activities remaining: [activitiesRemaining] of 10"`
  - Progress bar showing usage

- **Button**: "Upgrade to Premium"
  - **On Tap**: Navigate to `SubscriptionIntroPage`

### 7.3: Alternative - Use Bottom Sheet

Instead of a new page, show subscription details in a bottom sheet:

- [ ] **7.3.1** - Create component: `SubscriptionDetailsSheet`.

- [ ] **7.3.2** - On Settings page subscription item tap:
  - **Show Bottom Sheet** → `SubscriptionDetailsSheet`

---

## Section 8: Testing Checklist

### 8.1: Data Types & App State

- [ ] **8.1.1** - Verify `SubscriptionStatusStruct` compiles without errors.
- [ ] **8.1.2** - Verify `PromoValidationResponseStruct` is created correctly.
- [ ] **8.1.3** - Verify all App State variables are accessible in the UI.

### 8.2: API Calls

- [ ] **8.2.1** - Test `validatePromoCode` with:
  - Valid code → Returns `valid: true`, `offering_id`, `discount_percent`
  - Invalid code → Returns `valid: false`, `error` message
  - Empty code → Returns error

- [ ] **8.2.2** - Test `getSubscriptionStatus` with:
  - Premium user → Returns `is_premium: true`, populated fields
  - Free user → Returns `is_premium: false`, activity limits

### 8.3: Subscription Status Sync

- [ ] **8.3.1** - Log in with a fresh session → Verify `subscriptionStatus` is populated.
- [ ] **8.3.2** - Check `isPremium` and `activitiesRemaining` App State values.
- [ ] **8.3.3** - After purchase → Verify status is refreshed.

### 8.4: Promo Code Flow

- [ ] **8.4.1** - On SubscriptionIntroPage:
  - Enter valid promo → Green success message appears
  - Prices update to show discounted amounts
  - `appliedOfferingId` App State is set

- [ ] **8.4.2** - Enter invalid promo:
  - Red error message appears
  - Prices remain at full price
  - `appliedOfferingId` remains "default"

- [ ] **8.4.3** - Enter empty promo and tap Apply:
  - Shows appropriate error

### 8.5: Purchase Flow

- [ ] **8.5.1** - **Sandbox Testing (iOS)**:
  - Use Sandbox Apple ID
  - Tap Annual option → Purchase sheet appears
  - Complete purchase → Success message shown
  - `isPremium` becomes `true`
  - Navigated back to entry point

- [ ] **8.5.2** - **Sandbox Testing (Android)**:
  - Use test Google account
  - Same flow verification

- [ ] **8.5.3** - **Purchase with Promo**:
  - Apply valid promo code
  - Complete purchase
  - Verify correct offering was used (check RevenueCat dashboard)

- [ ] **8.5.4** - **Purchase Cancellation**:
  - Initiate purchase, then cancel
  - No error shown (user intentionally cancelled)
  - State unchanged

### 8.6: Subscription Management

- [ ] **8.6.1** - As free user:
  - Settings shows "Free" status
  - Tapping shows upgrade prompt
  - Activities remaining displayed correctly

- [ ] **8.6.2** - As premium user:
  - Settings shows "Premium" status
  - Correct plan and renewal date shown
  - "Manage Subscription" opens platform subscription page

### 8.7: Edge Cases

- [ ] **8.7.1** - Network offline during promo validation → Appropriate error shown.
- [ ] **8.7.2** - Network offline during purchase → RevenueCat handles gracefully.
- [ ] **8.7.3** - Expired subscription → `isPremium` is false, shows as free user.
- [ ] **8.7.4** - Cancelled but not expired → Shows "Access until [date]".

---

## Section 9: Firebase Analytics Events

Ensure these events are logged for tracking:

| Event Name | Parameters | Trigger |
|------------|------------|---------|
| `subscriptionIntropage_viewed` | - | Page load |
| `promo_code_applied` | `code`, `discount_percent` | Successful promo validation |
| `promo_code_failed` | `code`, `error` | Failed promo validation |
| `purchase_initiated` | `plan`, `promo_code` | Tap on purchase button |
| `purchase_completed` | `plan`, `promo_code`, `revenue` | Successful purchase |
| `purchase_failed` | `plan`, `error` | Failed purchase |
| `purchase_cancelled` | `plan` | User cancelled |

---

## References

1. [FlutterFlow RevenueCat Integration](https://docs.flutterflow.io/integrations/in-app-purchases-revenuecats)
2. [RevenueCat Web Purchase Button](https://www.revenuecat.com/docs/web-purchase-button)
3. [FlutterFlow Custom Actions](https://docs.flutterflow.io/customizing-your-app/custom-functions/custom-actions)
4. [FlutterFlow Conditional Builder](https://docs.flutterflow.io/widgets-and-components/widgets/layout-elements/conditional-builder)
5. [FlutterFlow App State](https://docs.flutterflow.io/advanced-functionality/app-state-and-page-state)

---

## Appendix A: API Response Examples

### Promo Validation Success
```json
{
  "valid": true,
  "code": "VANESSA",
  "discount_percent": 20,
  "influencer_name": "Vanessa Marin",
  "offering_id": "discounted_20_percent"
}
```

### Promo Validation Error
```json
{
  "valid": false,
  "error": "Code not found"
}
```

### Subscription Status (Premium)
```json
{
  "user_id": "uuid",
  "subscription_tier": "premium",
  "is_premium": true,
  "expires_at": "2026-02-22T00:00:00Z",
  "is_cancelled": false,
  "platform": "stripe",
  "product_id": "attuned_monthly_premium",
  "activities_used": 5,
  "activities_limit": 10,
  "activities_remaining": 5,
  "has_billing_issue": false,
  "promo_code_used": "VANESSA"
}
```

### Subscription Status (Free)
```json
{
  "user_id": "uuid",
  "subscription_tier": "free",
  "is_premium": false,
  "expires_at": null,
  "is_cancelled": false,
  "platform": null,
  "product_id": null,
  "activities_used": 3,
  "activities_limit": 10,
  "activities_remaining": 7,
  "has_billing_issue": false,
  "promo_code_used": null
}
```

---

## Appendix B: Deferred Features

The following were scoped out of this MVP:

1. **Activity Limit Enforcement** - Backend handles via game API returning `LIMIT_REACHED` card type
2. **Region Detection** - RevenueCat Web Purchase Button handles automatically
3. **Billing Issue Banner** - Deferred to post-MVP
4. **Restore Purchases Button** - Consider adding to Settings for users who reinstall

---

**Version**: 1.0
**Last Updated**: 2026-01-22
**Author**: Claude Code Assistant
