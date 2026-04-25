import { render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import FeaturedPanel from "../FeaturedPanel"

beforeEach(() => {
  global.fetch = jest.fn()
})

afterEach(() => {
  jest.resetAllMocks()
})


test("renders the featured panel header", async () => {
  global.fetch.mockResolvedValueOnce({
    json: async () => ({ satellites: [] }),
  })

  render(<FeaturedPanel onSelect={() => {}} />)

  expect(await screen.findByText(/featured/i)).toBeInTheDocument()
})


test("renders a featured satellite returned by the API", async () => {
  global.fetch.mockResolvedValueOnce({
    json: async () => ({
      satellites: [
        {
          norad_id: 25544,
          name: "ISS",
          group: "stations",
          tagline: "International Space Station",
          description: "The largest artificial object in space.",
          available: true,
        },
      ],
    }),
  })

  render(<FeaturedPanel onSelect={() => {}} />)

  expect(
    await screen.findByText("International Space Station")
  ).toBeInTheDocument()
  expect(
    screen.getByText(/largest artificial object/i)
  ).toBeInTheDocument()
})


test("calls onSelect when clicking an available satellite", async () => {
  const onSelect = jest.fn()

  global.fetch.mockResolvedValueOnce({
    json: async () => ({
      satellites: [
        {
          norad_id: 25544,
          name: "ISS",
          group: "stations",
          tagline: "International Space Station",
          description: "Test",
          available: true,
        },
      ],
    }),
  })

  render(<FeaturedPanel onSelect={onSelect} />)

  const entry = await screen.findByText("International Space Station")
  await userEvent.click(entry)

  expect(onSelect).toHaveBeenCalledWith(25544)
})


test("does not call onSelect for unavailable satellites", async () => {
  const onSelect = jest.fn()

  global.fetch.mockResolvedValueOnce({
    json: async () => ({
      satellites: [
        {
          norad_id: 99999,
          name: "MISSING",
          group: "unknown",
          tagline: "Unavailable Satellite",
          description: "Test",
          available: false,
        },
      ],
    }),
  })

  render(<FeaturedPanel onSelect={onSelect} />)

  const entry = await screen.findByText("Unavailable Satellite")
  await userEvent.click(entry)

  expect(onSelect).not.toHaveBeenCalled()
})


test("collapses when header is clicked", async () => {
  global.fetch.mockResolvedValueOnce({
    json: async () => ({
      satellites: [
        {
          norad_id: 25544,
          name: "ISS",
          group: "stations",
          tagline: "International Space Station",
          description: "Test",
          available: true,
        },
      ],
    }),
  })

  render(<FeaturedPanel onSelect={() => {}} />)

  expect(
    await screen.findByText("International Space Station")
  ).toBeInTheDocument()

  const header = screen.getByText(/featured/i)
  await userEvent.click(header)

  await waitFor(() => {
    expect(
      screen.queryByText("International Space Station")
    ).not.toBeInTheDocument()
  })
})