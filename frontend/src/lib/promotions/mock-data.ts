import { isoDate } from "./status";
import type { BankCode, CategorySlug, DiscountType, Promotion } from "./types";

/**
 * Sample offers used until the scraper API exists. They are illustrative, not
 * real bank offers. Dates are stored as day offsets from "now" so the set
 * always contains a realistic mix of active, upcoming and expired offers.
 */
interface MockSeed {
  bank: BankCode;
  merchant: string;
  title: string;
  description: string;
  category: CategorySlug;
  bank_category: string;
  discount: [DiscountType, number] | null;
  cards: string[];
  /** Validity window as day offsets from today; `null` end = open-ended. */
  from: number;
  to: number | null;
  /** Days ago the scraper first saw the offer. */
  seen: number;
  /** Set when the offer has disappeared from the bank's site. */
  gone?: boolean;
}

const SOURCE_URLS: Record<BankCode, string> = {
  combank: "https://www.combank.lk/rewards-promotions",
  sampath: "https://www.sampath.lk/sampath-cards/credit-card-offer?firstTab=Other",
};

const VISA_MC = ["Visa", "Mastercard"];

const SEEDS: MockSeed[] = [
  { bank: "combank", merchant: "Ministry of Crab", title: "20% off your total bill", description: "Enjoy 20% off the total bill for dine-in on weekdays. Reservations recommended. Not valid on public holidays or with other promotions.", category: "dining", bank_category: "Food & Restaurants", discount: ["percentage", 20], cards: ["Visa Signature", "Mastercard World"], from: -10, to: 25, seen: 9 },
  { bank: "sampath", merchant: "Pizza Hut", title: "Buy one, get one free on large pizzas", description: "Order any large pan pizza and get a second one free on Wednesdays. Valid for dine-in, takeaway and delivery through the Pizza Hut app.", category: "dining", bank_category: "Dining", discount: null, cards: VISA_MC, from: -3, to: 40, seen: 2 },
  { bank: "combank", merchant: "Keells", title: "15% off groceries every Friday", description: "Save 15% on grocery bills over Rs. 7,500 at all Keells outlets on Fridays. Maximum discount of Rs. 3,000 per card per day.", category: "supermarket", bank_category: "Supermarkets", discount: ["percentage", 15], cards: VISA_MC, from: -20, to: 10, seen: 19 },
  { bank: "sampath", merchant: "Cargills Food City", title: "Rs. 1,000 off weekend shopping", description: "Get Rs. 1,000 off when you spend Rs. 10,000 or more on Saturdays and Sundays at Cargills Food City and FoodHall.", category: "supermarket", bank_category: "Supermarkets", discount: ["fixed", 1000], cards: ["Visa", "Mastercard", "Amex"], from: -5, to: 3, seen: 4 },
  { bank: "combank", merchant: "Arpico Supercentre", title: "10% off on Mondays", description: "Spend Rs. 5,000 or more on a Monday and get 10% off. Capped at Rs. 2,500 per transaction.", category: "supermarket", bank_category: "Supermarkets", discount: ["percentage", 10], cards: VISA_MC, from: -45, to: -2, seen: 44, gone: true },
  { bank: "combank", merchant: "SriLankan Airlines", title: "12% off return tickets to Asia", description: "Book return economy and business class tickets from Colombo to destinations across Asia and save 12% on the base fare. Travel must be completed within six months of booking.", category: "travel", bank_category: "Travel & Leisure", discount: ["percentage", 12], cards: ["Visa Infinite", "Mastercard World"], from: -7, to: 60, seen: 6 },
  { bank: "sampath", merchant: "Booking.com", title: "8% cashback on hotel bookings", description: "Receive 8% cashback on hotel stays booked through the Booking.com partner link. Cashback is credited within 45 days of checkout.", category: "online", bank_category: "Online", discount: ["percentage", 8], cards: VISA_MC, from: -12, to: 80, seen: 11 },
  { bank: "combank", merchant: "Cinnamon Grand Colombo", title: "25% off rooms and dining", description: "Enjoy 25% off the best available room rate and at selected restaurants. Valid for stays from Sunday to Thursday.", category: "hotels", bank_category: "Hotels", discount: ["percentage", 25], cards: ["Visa Platinum", "Mastercard Titanium"], from: 5, to: 50, seen: 1 },
  { bank: "sampath", merchant: "Jetwing Hotels", title: "30% off island-wide stays", description: "Save up to 30% on full-board and half-board stays at Jetwing hotels across Sri Lanka. Subject to room availability.", category: "hotels", bank_category: "Hotels & Resorts", discount: ["percentage", 30], cards: VISA_MC, from: -15, to: 15, seen: 14 },
  { bank: "combank", merchant: "Hilton Colombo", title: "Weekend brunch at 20% off", description: "Bring the family for Sunday brunch at Graze Kitchen and save 20%. Valid for up to 10 guests per card.", category: "dining", bank_category: "Food & Restaurants", discount: ["percentage", 20], cards: VISA_MC, from: -30, to: 1, seen: 29 },
  { bank: "sampath", merchant: "Odel", title: "20% off fashion and lifestyle", description: "Get 20% off on fashion, beauty and home items at all Odel stores. Not valid on already discounted items.", category: "fashion", bank_category: "Clothing & Fashion", discount: ["percentage", 20], cards: VISA_MC, from: -2, to: 28, seen: 1 },
  { bank: "combank", merchant: "Fashion Bug", title: "15% off new arrivals", description: "Save 15% on new season arrivals at Fashion Bug outlets and online. Minimum spend Rs. 6,000.", category: "fashion", bank_category: "Fashion", discount: ["percentage", 15], cards: VISA_MC, from: 10, to: 40, seen: 0 },
  { bank: "sampath", merchant: "Cool Planet", title: "Rs. 2,500 off on Rs. 15,000", description: "Spend Rs. 15,000 or more in a single bill at Cool Planet and get Rs. 2,500 off instantly.", category: "fashion", bank_category: "Clothing & Fashion", discount: ["fixed", 2500], cards: VISA_MC, from: -25, to: -1, seen: 24 },
  { bank: "combank", merchant: "Abans", title: "0% installments for 24 months", description: "Buy TVs, refrigerators and home appliances on 0% interest easy payment plans for up to 24 months. Minimum transaction Rs. 50,000.", category: "electronics", bank_category: "Electronics & Appliances", discount: ["installment", 24], cards: VISA_MC, from: -60, to: 120, seen: 59 },
  { bank: "sampath", merchant: "Singer", title: "0% installments for 12 months", description: "Pay for laptops, phones and appliances over 12 months at 0% interest at all Singer Mega showrooms.", category: "electronics", bank_category: "Electronics", discount: ["installment", 12], cards: VISA_MC, from: -8, to: 52, seen: 7 },
  { bank: "combank", merchant: "Softlogic", title: "10% off smartphones", description: "Save 10% on selected Samsung and Apple smartphones at Softlogic MAX stores. Maximum discount Rs. 25,000.", category: "electronics", bank_category: "Electronics & Appliances", discount: ["percentage", 10], cards: ["Visa Signature", "Mastercard World"], from: -1, to: 6, seen: 0 },
  { bank: "sampath", merchant: "Damro", title: "0% installments for 36 months", description: "Furnish your home with 36 months of 0% interest installments on furniture and electronics at Damro.", category: "electronics", bank_category: "Furniture & Electronics", discount: ["installment", 36], cards: VISA_MC, from: 3, to: 90, seen: 2 },
  { bank: "combank", merchant: "Asiri Hospitals", title: "15% off health checks", description: "Get 15% off comprehensive health screening packages at Asiri Central, Surgical and Medical hospitals.", category: "health", bank_category: "Health & Wellness", discount: ["percentage", 15], cards: VISA_MC, from: -40, to: 50, seen: 39 },
  { bank: "sampath", merchant: "Healthguard Pharmacy", title: "10% off pharmacy bills", description: "Save 10% on medicine and wellness products at Healthguard outlets. Capped at Rs. 1,500 per transaction.", category: "health", bank_category: "Health", discount: ["percentage", 10], cards: VISA_MC, from: -18, to: 12, seen: 17 },
  { bank: "combank", merchant: "Lanka IOC", title: "5% cashback on fuel", description: "Get 5% cashback on fuel at Lanka IOC stations on weekends. Maximum cashback Rs. 1,000 per month.", category: "fuel", bank_category: "Fuel", discount: ["percentage", 5], cards: VISA_MC, from: -90, to: null, seen: 88 },
  { bank: "sampath", merchant: "Ceypetco", title: "Rs. 500 off fuel over Rs. 10,000", description: "Fill up for Rs. 10,000 or more at participating Ceypetco stations and get Rs. 500 off.", category: "fuel", bank_category: "Fuel", discount: ["fixed", 500], cards: VISA_MC, from: -6, to: 24, seen: 5 },
  { bank: "combank", merchant: "Daraz", title: "Up to 18% off on Daraz", description: "Save up to 18% on electronics, fashion and home categories during Daraz mega sale days. Discount is applied at checkout.", category: "online", bank_category: "Online", discount: ["percentage", 18], cards: VISA_MC, from: -4, to: 2, seen: 3 },
  { bank: "sampath", merchant: "PickMe Food", title: "25% off food delivery", description: "Get 25% off food orders over Rs. 2,000 on PickMe Food, up to Rs. 750 per order. Valid twice per card per week.", category: "online", bank_category: "Online & Delivery", discount: ["percentage", 25], cards: VISA_MC, from: -9, to: 21, seen: 8 },
  { bank: "combank", merchant: "Kapruka", title: "Rs. 1,500 off gift orders", description: "Send gifts island-wide with Rs. 1,500 off orders of Rs. 12,000 or more on Kapruka.com.", category: "online", bank_category: "Online", discount: ["fixed", 1500], cards: VISA_MC, from: 7, to: 37, seen: 0 },
  { bank: "sampath", merchant: "Barista", title: "Buy 2 coffees, get 1 free", description: "Order any two handcrafted beverages and get a third free at Barista cafés island-wide.", category: "dining", bank_category: "Dining", discount: null, cards: VISA_MC, from: -14, to: 16, seen: 13 },
  { bank: "combank", merchant: "Colombo City Centre", title: "Rs. 3,000 off when you spend Rs. 20,000", description: "Spend across stores in Colombo City Centre on the same day and redeem a Rs. 3,000 voucher at the concierge.", category: "other", bank_category: "Lifestyle", discount: ["fixed", 3000], cards: ["Visa Infinite", "Mastercard World Elite"], from: -11, to: 19, seen: 10 },
  { bank: "sampath", merchant: "Scope Cinemas", title: "50% off movie tickets", description: "Get 50% off up to two tickets per transaction at Scope Cinemas on Tuesdays and Wednesdays.", category: "other", bank_category: "Entertainment", discount: ["percentage", 50], cards: VISA_MC, from: -21, to: 9, seen: 20 },
  { bank: "combank", merchant: "Mövenpick Colombo", title: "Seafood night at 30% off", description: "Enjoy 30% off the Friday seafood buffet at Mövenpick Colombo. Prior reservation required.", category: "dining", bank_category: "Food & Restaurants", discount: ["percentage", 30], cards: VISA_MC, from: -50, to: -10, seen: 49, gone: true },
];

function shiftDays(now: Date, days: number): string {
  return isoDate(new Date(now.getTime() + days * 86_400_000));
}

export function buildMockPromotions(now: Date): Promotion[] {
  return SEEDS.map((seed, index) => {
    const seenAt = new Date(now.getTime() - seed.seen * 86_400_000 - index * 60_000);
    // Offers that left the site were last seen on their final day.
    const lastSeenAt =
      seed.gone && seed.to !== null
        ? new Date(now.getTime() + seed.to * 86_400_000)
        : now;
    return {
      id: String(index + 1),
      bank: seed.bank,
      title: seed.title,
      merchant: seed.merchant,
      description: seed.description,
      discount_type: seed.discount?.[0] ?? null,
      discount_value: seed.discount?.[1] ?? null,
      card_types: seed.cards,
      category: seed.category,
      bank_category: seed.bank_category,
      valid_from: shiftDays(now, seed.from),
      valid_to: seed.to === null ? null : shiftDays(now, seed.to),
      image_url: null,
      source_url: SOURCE_URLS[seed.bank],
      first_seen_at: seenAt.toISOString(),
      last_seen_at: lastSeenAt.toISOString(),
      is_active: !seed.gone,
    };
  });
}
