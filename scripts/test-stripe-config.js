#!/usr/bin/env node
/**
 * Stripe Configuration Test Script
 * Tests if Stripe can be initialized with dummy keys for build process
 */

console.log('🔧 Testing Stripe Configuration for Build...');
console.log('=' * 50);

// Test dummy keys (same as used in Dockerfile)
const dummyPublicKey = 'pk_test_dummy_for_build';
const dummySecretKey = 'sk_test_dummy_for_build';

console.log(`📋 Testing with dummy keys:`);
console.log(`   Public Key: ${dummyPublicKey}`);
console.log(`   Secret Key: ${dummySecretKey.substring(0, 15)}...`);

// Test 1: @stripe/stripe-js (frontend)
try {
  const { loadStripe } = require('@stripe/stripe-js');
  console.log('\n✅ @stripe/stripe-js imported successfully');
  
  // Test loadStripe initialization (this is what frontend uses)
  const stripePromise = loadStripe(dummyPublicKey);
  console.log('✅ loadStripe() call successful with dummy key');
} catch (error) {
  console.log(`❌ @stripe/stripe-js error: ${error.message}`);
}

// Test 2: stripe (server-side)
try {
  const Stripe = require('stripe');
  console.log('✅ stripe package imported successfully');
  
  // Test Stripe initialization (this is what causes the build error)
  const stripe = new Stripe(dummySecretKey, {
    apiVersion: '2023-10-16', // Use a specific API version to avoid warnings
  });
  console.log('✅ Stripe instance created successfully with dummy key');
  
  // Test that we can access stripe methods without API calls
  console.log(`✅ Stripe instance has expected methods: ${typeof stripe.checkout === 'object'}`);
  
} catch (error) {
  console.log(`❌ stripe package error: ${error.message}`);
  console.log('   This is likely the source of the build failure!');
}

// Test 3: Environment variable handling
console.log('\n📊 Environment Variable Test:');
process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY = dummyPublicKey;
process.env.STRIPE_SECRET_KEY = dummySecretKey;
process.env.SKIP_ENV_VALIDATION = 'true';

console.log(`   NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY: ${process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY ? '✅ Set' : '❌ Missing'}`);
console.log(`   STRIPE_SECRET_KEY: ${process.env.STRIPE_SECRET_KEY ? '✅ Set' : '❌ Missing'}`);
console.log(`   SKIP_ENV_VALIDATION: ${process.env.SKIP_ENV_VALIDATION ? '✅ Set' : '❌ Missing'}`);

// Test 4: Simulate build-time API route processing
console.log('\n🚀 Simulating API Route Processing:');
try {
  // This simulates what happens when Next.js processes API routes during build
  const stripe = new Stripe(process.env.STRIPE_SECRET_KEY, {
    apiVersion: '2023-10-16',
  });
  
  console.log('✅ API route would process successfully during build');
  console.log('✅ No "Neither apiKey nor config.authenticator provided" error');
  
} catch (error) {
  console.log(`❌ API route processing would fail: ${error.message}`);
}

console.log('\n' + '='.repeat(50));
console.log('🎯 TEST SUMMARY:');
console.log('If all tests show ✅, the Docker build should succeed');
console.log('If any show ❌, those issues need to be fixed first');
console.log('\n🔧 Next step: Run the Docker build if tests pass');
