import type { Config } from "tailwindcss";

export default {
	darkMode: ["class"],
	content: [
		"./pages/**/*.{ts,tsx}",
		"./components/**/*.{ts,tsx}",
		"./app/**/*.{ts,tsx}",
		"./src/**/*.{ts,tsx}",
	],
	prefix: "",
	theme: {
		container: {
			center: true,
			padding: '2rem',
			screens: {
				'2xl': '1400px'
			}
		},
		extend: {
			fontFamily: {
				sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', '"Segoe UI"', 'sans-serif'],
			},
			maxWidth: {
				content: '720px',
				page: '1200px',
				consultation: '880px',
			},
			colors: {
				healia: {
					bg: '#F8F8F5',
					'bg-secondary': '#FFFFFF',
					text: '#17201D',
					'text-secondary': '#5F6965',
					'text-muted': '#87918D',
					brand: '#155E59',
					'brand-dark': '#104944',
					'brand-light': '#E6F1EF',
					border: '#DDE3E0',
					'border-subtle': '#E9EDEB',
					success: '#2F6F55',
					warning: '#9A6A20',
					danger: '#B54747',
					info: '#356A82',
				},
				border: 'hsl(var(--border))',
				input: 'hsl(var(--input))',
				ring: 'hsl(var(--ring))',
				background: 'hsl(var(--background))',
				foreground: 'hsl(var(--foreground))',
				primary: {
					DEFAULT: 'hsl(var(--primary))',
					foreground: 'hsl(var(--primary-foreground))'
				},
				secondary: {
					DEFAULT: 'hsl(var(--secondary))',
					foreground: 'hsl(var(--secondary-foreground))'
				},
				destructive: {
					DEFAULT: 'hsl(var(--destructive))',
					foreground: 'hsl(var(--destructive-foreground))'
				},
				muted: {
					DEFAULT: 'hsl(var(--muted))',
					foreground: 'hsl(var(--muted-foreground))'
				},
				accent: {
					DEFAULT: 'hsl(var(--accent))',
					foreground: 'hsl(var(--accent-foreground))'
				},
				popover: {
					DEFAULT: 'hsl(var(--popover))',
					foreground: 'hsl(var(--popover-foreground))'
				},
				card: {
					DEFAULT: 'hsl(var(--card))',
					foreground: 'hsl(var(--card-foreground))'
				},
				sidebar: {
					DEFAULT: 'hsl(var(--sidebar-background))',
					foreground: 'hsl(var(--sidebar-foreground))',
					primary: 'hsl(var(--sidebar-primary))',
					'primary-foreground': 'hsl(var(--sidebar-primary-foreground))',
					accent: 'hsl(var(--sidebar-accent))',
					'accent-foreground': 'hsl(var(--sidebar-accent-foreground))',
					border: 'hsl(var(--sidebar-border))',
					ring: 'hsl(var(--sidebar-ring))'
				}
			},
			borderRadius: {
				lg: 'var(--radius)',
				md: 'calc(var(--radius) - 2px)',
				sm: 'calc(var(--radius) - 4px)'
			},
			keyframes: {
				'accordion-down': {
					from: {
						height: '0'
					},
					to: {
						height: 'var(--radix-accordion-content-height)'
					}
				},
				'accordion-up': {
					from: {
						height: 'var(--radix-accordion-content-height)'
					},
					to: {
						height: '0'
					}
				},
				'healia-ring': {
					'0%': { transform: 'scale(1)', opacity: '0.55' },
					'70%': { transform: 'scale(1.18)', opacity: '0' },
					'100%': { transform: 'scale(1.18)', opacity: '0' }
				},
				'healia-ring-slow': {
					'0%': { transform: 'scale(1)', opacity: '0.4' },
					'70%': { transform: 'scale(1.12)', opacity: '0' },
					'100%': { transform: 'scale(1.12)', opacity: '0' }
				},
				'healia-spark': {
					'0%, 100%': { opacity: '0.2', transform: 'scale(0.8)' },
					'50%': { opacity: '0.9', transform: 'scale(1.35)' }
				}
			},
			animation: {
				'accordion-down': 'accordion-down 0.2s ease-out',
				'accordion-up': 'accordion-up 0.2s ease-out',
				'healia-ring': 'healia-ring 1.6s ease-out infinite',
				'healia-ring-delay': 'healia-ring 1.6s ease-out 0.35s infinite',
				'healia-ring-slow': 'healia-ring-slow 2.4s ease-out infinite',
				'healia-spark': 'healia-spark 1.1s ease-in-out infinite'
			}
		}
	},
	plugins: [require("tailwindcss-animate")],
} satisfies Config;
